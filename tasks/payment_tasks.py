"""Celery tasks for payment processing and reconciliation."""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=2, retry_backoff=True)
def process_payment(self, payment_id: str):
    """Process a pending payment through Stripe with exponential backoff.

    Retry delays: 2s, 4s, 8s (max 3 retries).
    """
    from apps.payments.models import Payment
    from apps.payments.services import PaymentService, ServiceUnavailableError

    try:
        payment = Payment.objects.get(id=payment_id)
    except Payment.DoesNotExist:
        logger.error("Payment %s not found", payment_id)
        return

    if payment.status != Payment.Status.PENDING:
        logger.info("Payment %s already processed (status=%s)", payment_id, payment.status)
        return

    service = PaymentService()
    try:
        service.create_payment(payment)
        logger.info("Payment %s completed successfully", payment_id)
    except ServiceUnavailableError as e:
        logger.warning("Payment processor unavailable for payment %s, retrying", payment_id)
        raise self.retry(exc=e)
    except Exception as e:
        logger.exception("Payment %s failed permanently", payment_id)


@shared_task
def reconcile_payments():
    """Reconcile pending payments that may have stale status.

    Runs hourly. Checks payments that have been pending for > 30 minutes
    and verifies their status with Stripe.
    """
    from datetime import timedelta

    from django.utils import timezone

    from apps.payments.models import Payment

    threshold = timezone.now() - timedelta(minutes=30)
    stale_payments = Payment.objects.filter(
        status=Payment.Status.PENDING,
        created_at__lt=threshold,
    )

    count = stale_payments.count()
    if count > 0:
        logger.info("Found %d stale pending payments for reconciliation", count)

    for payment in stale_payments[:100]:  # Process max 100 at a time
        try:
            _reconcile_single(payment)
        except Exception:
            logger.exception("Failed to reconcile payment %s", payment.id)


def _reconcile_single(payment):
    """Check a single payment status with Stripe."""
    import stripe
    from django.conf import settings

    from apps.payments.models import Payment

    if not payment.processor_ref:
        payment.status = Payment.Status.FAILED
        payment.metadata["reconciliation"] = "No processor reference"
        payment.save(update_fields=["status", "metadata"])
        return

    stripe.api_key = settings.STRIPE_API_KEY
    try:
        intent = stripe.PaymentIntent.retrieve(payment.processor_ref)
        if intent.status == "succeeded":
            payment.status = Payment.Status.COMPLETED
        elif intent.status in ("canceled", "requires_payment_method"):
            payment.status = Payment.Status.FAILED
        payment.metadata["reconciled"] = True
        payment.save(update_fields=["status", "metadata"])
    except stripe.error.StripeError as e:
        logger.warning("Stripe API error during reconciliation of payment %s: %s", payment.id, e)
