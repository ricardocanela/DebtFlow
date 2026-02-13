"""Payment business logic: Stripe client, circuit breaker, payment processing."""
import logging
import time
from decimal import Decimal

import stripe
from django.conf import settings
from django.core.cache import cache
from django.db import transaction

from apps.accounts.models import Account, Activity

from .models import Payment

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Redis-backed circuit breaker for external API calls.

    States: closed (normal), open (failing), half_open (testing recovery).
    - Opens after `failure_threshold` failures within `window_seconds`.
    - Attempts half-open after `recovery_timeout` seconds.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        window_seconds: int = 60,
        recovery_timeout: int = 30,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.window_seconds = window_seconds
        self.recovery_timeout = recovery_timeout
        self._state_key = f"circuit_breaker:{name}:state"
        self._failure_key = f"circuit_breaker:{name}:failures"
        self._opened_at_key = f"circuit_breaker:{name}:opened_at"

    @property
    def state(self) -> str:
        state = cache.get(self._state_key, "closed")
        if state == "open":
            opened_at = cache.get(self._opened_at_key, 0)
            if time.time() - opened_at >= self.recovery_timeout:
                return "half_open"
        return state

    def record_success(self):
        cache.set(self._state_key, "closed", timeout=self.window_seconds * 10)
        cache.delete(self._failure_key)

    def record_failure(self):
        failures = cache.get(self._failure_key, 0) + 1
        cache.set(self._failure_key, failures, timeout=self.window_seconds)
        if failures >= self.failure_threshold:
            cache.set(self._state_key, "open", timeout=self.recovery_timeout * 10)
            cache.set(self._opened_at_key, time.time(), timeout=self.recovery_timeout * 10)
            logger.warning("Circuit breaker '%s' OPENED after %d failures", self.name, failures)

    def is_available(self) -> bool:
        return self.state != "open"


# Singleton circuit breaker for Stripe
stripe_circuit_breaker = CircuitBreaker("stripe", failure_threshold=5, window_seconds=60, recovery_timeout=30)


class StripeClient:
    """Wrapper around the Stripe SDK with circuit breaker and idempotency."""

    def __init__(self):
        stripe.api_key = settings.STRIPE_API_KEY

    def create_charge(self, amount: Decimal, idempotency_key: str, metadata: dict | None = None) -> dict:
        """Create a Stripe PaymentIntent."""
        if not stripe_circuit_breaker.is_available():
            raise ServiceUnavailableError("Payment processor is temporarily unavailable. Please retry later.")

        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Stripe uses cents
                currency="usd",
                metadata=metadata or {},
                idempotency_key=idempotency_key,
            )
            stripe_circuit_breaker.record_success()
            return {"id": intent.id, "status": intent.status, "client_secret": intent.client_secret}
        except stripe.error.StripeError as e:
            stripe_circuit_breaker.record_failure()
            logger.error("Stripe API error: %s", str(e))
            raise

    def create_refund(self, payment_intent_id: str, reason: str = "") -> dict:
        """Refund a Stripe PaymentIntent."""
        if not stripe_circuit_breaker.is_available():
            raise ServiceUnavailableError("Payment processor is temporarily unavailable.")

        try:
            refund = stripe.Refund.create(payment_intent=payment_intent_id, reason="requested_by_customer")
            stripe_circuit_breaker.record_success()
            return {"id": refund.id, "status": refund.status}
        except stripe.error.StripeError as e:
            stripe_circuit_breaker.record_failure()
            logger.error("Stripe refund error: %s", str(e))
            raise


class ServiceUnavailableError(Exception):
    pass


class PaymentService:
    """Orchestrates payment creation with idempotency and Stripe integration."""

    def __init__(self):
        self.stripe_client = StripeClient()

    def create_payment(self, payment: Payment) -> Payment:
        """Process a new payment through Stripe."""
        # Check idempotency via Redis
        cache_key = f"idempotency:{payment.idempotency_key}"
        if cache.get(cache_key):
            existing = Payment.objects.filter(idempotency_key=payment.idempotency_key).first()
            if existing:
                return existing

        payment.status = Payment.Status.PENDING
        payment.save()

        # Set idempotency key in Redis (24h TTL)
        cache.set(cache_key, str(payment.id), timeout=86400)

        try:
            result = self.stripe_client.create_charge(
                amount=payment.amount,
                idempotency_key=payment.idempotency_key,
                metadata={"account_id": str(payment.account_id), "payment_id": str(payment.id)},
            )
        except ServiceUnavailableError:
            payment.status = Payment.Status.FAILED
            payment.metadata = {"error": "Payment processor unavailable"}
            payment.save(update_fields=["status", "metadata"])
            raise
        except Exception as e:
            payment.status = Payment.Status.FAILED
            payment.metadata = {"error": str(e)}
            payment.save(update_fields=["status", "metadata"])
            raise

        # Success path: update payment + account balance atomically
        with transaction.atomic():
            payment.processor_ref = result["id"]
            payment.status = Payment.Status.COMPLETED
            payment.metadata = result
            payment.save(update_fields=["processor_ref", "status", "metadata"])

            account = Account.objects.select_for_update().get(id=payment.account_id)
            account.current_balance = max(Decimal("0"), account.current_balance - payment.amount)
            account.save(update_fields=["current_balance", "updated_at"])

            Activity.objects.create(
                account=account,
                activity_type=Activity.ActivityType.PAYMENT,
                description=f"Payment of ${payment.amount} received via {payment.payment_method}",
                metadata={"payment_id": str(payment.id), "processor_ref": result["id"]},
            )

        return payment

    @transaction.atomic
    def refund_payment(self, payment: Payment, reason: str = "") -> Payment:
        """Refund a completed payment."""
        if payment.status != Payment.Status.COMPLETED:
            raise ValueError(f"Cannot refund payment with status '{payment.status}'")

        result = self.stripe_client.create_refund(payment.processor_ref, reason)
        payment.status = Payment.Status.REFUNDED
        payment.metadata["refund"] = result
        payment.save(update_fields=["status", "metadata"])

        # Restore account balance
        account = Account.objects.select_for_update().get(id=payment.account_id)
        account.current_balance += payment.amount
        account.save(update_fields=["current_balance", "updated_at"])

        Activity.objects.create(
            account=account,
            activity_type=Activity.ActivityType.PAYMENT,
            description=f"Refund of ${payment.amount} processed. Reason: {reason}",
            metadata={"payment_id": str(payment.id), "refund_id": result["id"]},
        )

        return payment
