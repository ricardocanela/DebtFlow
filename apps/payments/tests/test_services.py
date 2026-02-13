"""Tests for payment services — circuit breaker, idempotency, PaymentService."""
import time
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.core.cache import cache

from apps.accounts.models import Account, Activity
from apps.accounts.tests.factories import AccountFactory
from apps.payments.models import Payment
from apps.payments.services import CircuitBreaker, PaymentService, ServiceUnavailableError

from .factories import PaymentFactory


class TestCircuitBreaker:
    def setup_method(self):
        cache.clear()
        self.cb = CircuitBreaker("test", failure_threshold=3, window_seconds=60, recovery_timeout=5)

    def test_initial_state_is_closed(self):
        assert self.cb.state == "closed"
        assert self.cb.is_available() is True

    def test_opens_after_threshold_failures(self):
        for _ in range(3):
            self.cb.record_failure()
        assert self.cb.state == "open"
        assert self.cb.is_available() is False

    def test_stays_closed_below_threshold(self):
        self.cb.record_failure()
        self.cb.record_failure()
        assert self.cb.state == "closed"
        assert self.cb.is_available() is True

    def test_success_resets_failures(self):
        self.cb.record_failure()
        self.cb.record_failure()
        self.cb.record_success()
        assert self.cb.state == "closed"

        # Should need 3 more failures to open
        self.cb.record_failure()
        self.cb.record_failure()
        assert self.cb.is_available() is True

    def test_half_open_after_recovery_timeout(self):
        for _ in range(3):
            self.cb.record_failure()
        assert self.cb.state == "open"

        # Simulate time passage by manipulating opened_at
        cache.set(self.cb._opened_at_key, time.time() - 10, timeout=300)
        assert self.cb.state == "half_open"
        assert self.cb.is_available() is True  # half_open allows requests


@pytest.mark.django_db
class TestPaymentService:
    @patch("apps.payments.services.stripe")
    def test_create_payment_success(self, mock_stripe):
        """Payment creation should charge Stripe, update status, and reduce account balance."""
        cache.clear()
        mock_intent = MagicMock()
        mock_intent.id = "pi_svc_test"
        mock_intent.status = "succeeded"
        mock_intent.client_secret = "secret"
        mock_stripe.PaymentIntent.create.return_value = mock_intent

        account = AccountFactory(current_balance=Decimal("1000.00"))
        payment = PaymentFactory(account=account, amount=Decimal("300.00"))

        service = PaymentService()
        result = service.create_payment(payment)

        assert result.status == Payment.Status.COMPLETED
        assert result.processor_ref == "pi_svc_test"

        # Account balance should be reduced
        account.refresh_from_db()
        assert account.current_balance == Decimal("700.00")

        # Activity should be created
        assert Activity.objects.filter(
            account=account,
            activity_type=Activity.ActivityType.PAYMENT,
        ).exists()

    @patch("apps.payments.services.stripe")
    def test_create_payment_stripe_failure(self, mock_stripe):
        """When Stripe fails, payment should be marked as FAILED."""
        cache.clear()
        mock_stripe.PaymentIntent.create.side_effect = Exception("Stripe error")
        mock_stripe.error.StripeError = type("StripeError", (Exception,), {})

        account = AccountFactory(current_balance=Decimal("1000.00"))
        payment = PaymentFactory(account=account, amount=Decimal("200.00"))

        service = PaymentService()
        with pytest.raises(Exception):
            service.create_payment(payment)

        payment.refresh_from_db()
        assert payment.status == Payment.Status.FAILED

        # Account balance should NOT change on failure
        account.refresh_from_db()
        assert account.current_balance == Decimal("1000.00")

    @patch("apps.payments.services.stripe")
    def test_refund_payment_restores_balance(self, mock_stripe):
        """Refund should restore account balance."""
        cache.clear()
        mock_refund = MagicMock()
        mock_refund.id = "re_svc_test"
        mock_refund.status = "succeeded"
        mock_stripe.Refund.create.return_value = mock_refund

        account = AccountFactory(current_balance=Decimal("500.00"))
        payment = PaymentFactory(
            account=account,
            amount=Decimal("200.00"),
            status=Payment.Status.COMPLETED,
            processor_ref="pi_refund_test",
        )

        service = PaymentService()
        result = service.refund_payment(payment, "Customer request")

        assert result.status == Payment.Status.REFUNDED
        account.refresh_from_db()
        assert account.current_balance == Decimal("700.00")

    def test_refund_non_completed_raises(self):
        """Cannot refund a payment that isn't completed."""
        payment = PaymentFactory(status=Payment.Status.PENDING)
        service = PaymentService()
        with pytest.raises(ValueError, match="Cannot refund"):
            service.refund_payment(payment)

    @patch("apps.payments.services.stripe_circuit_breaker")
    def test_circuit_breaker_blocks_payment(self, mock_cb):
        """When circuit breaker is open, payment should fail with ServiceUnavailableError."""
        mock_cb.is_available.return_value = False
        payment = PaymentFactory()

        service = PaymentService()
        with pytest.raises(ServiceUnavailableError):
            service.create_payment(payment)

    @patch("apps.payments.services.stripe")
    def test_idempotency_prevents_duplicate(self, mock_stripe):
        """Same idempotency key should not process twice."""
        cache.clear()
        mock_intent = MagicMock()
        mock_intent.id = "pi_idem_test"
        mock_intent.status = "succeeded"
        mock_intent.client_secret = "secret"
        mock_stripe.PaymentIntent.create.return_value = mock_intent

        account = AccountFactory(current_balance=Decimal("1000.00"))
        payment = PaymentFactory(account=account, amount=Decimal("100.00"))

        service = PaymentService()
        result1 = service.create_payment(payment)
        assert result1.status == Payment.Status.COMPLETED

        # Try to process the same payment again (same idempotency key in Redis)
        result2 = service.create_payment(payment)

        # Should return the original payment without calling Stripe again
        assert str(result2.id) == str(payment.id)
        # Stripe should only have been called once
        assert mock_stripe.PaymentIntent.create.call_count == 1
