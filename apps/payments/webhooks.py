"""Stripe webhook handler with HMAC validation and idempotency."""
import hashlib
import hmac
import json
import logging
import time

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.accounts.models import Activity

from .models import Payment

logger = logging.getLogger(__name__)

HANDLED_EVENTS = {
    "payment_intent.succeeded",
    "payment_intent.payment_failed",
    "charge.refunded",
    "charge.dispute.created",
}


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Receive and process Stripe webhook events.

    - Validates HMAC-SHA256 signature
    - Deduplicates events via Redis (event ID)
    - Updates payment status based on event type
    """
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

    # Validate signature
    if not _verify_signature(payload, sig_header):
        logger.warning("Stripe webhook: invalid signature")
        return JsonResponse({"error": "Invalid signature"}, status=400)

    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid payload"}, status=400)

    event_id = event.get("id", "")
    event_type = event.get("type", "")

    # Idempotency: skip duplicate events
    cache_key = f"stripe_event:{event_id}"
    if cache.get(cache_key):
        logger.info("Stripe webhook: duplicate event %s, skipping", event_id)
        return JsonResponse({"status": "already_processed"})

    # Mark event as processed (24h TTL)
    cache.set(cache_key, True, timeout=86400)

    if event_type not in HANDLED_EVENTS:
        logger.info("Stripe webhook: unhandled event type %s", event_type)
        return JsonResponse({"status": "ignored"})

    logger.info("Stripe webhook: processing event %s (%s)", event_id, event_type)

    try:
        _handle_event(event_type, event.get("data", {}).get("object", {}))
    except Exception:
        logger.exception("Stripe webhook: error processing event %s", event_id)
        # Don't return error — Stripe will retry. We already marked as processed.

    return JsonResponse({"status": "processed"})


def _verify_signature(payload: bytes, sig_header: str) -> bool:
    """Verify Stripe webhook HMAC-SHA256 signature."""
    if not sig_header:
        return False

    try:
        elements = dict(item.split("=", 1) for item in sig_header.split(","))
        timestamp = elements.get("t", "")
        signature = elements.get("v1", "")

        if not timestamp or not signature:
            return False

        # Check timestamp is within 5 minutes
        if abs(time.time() - int(timestamp)) > 300:
            return False

        signed_payload = f"{timestamp}.".encode() + payload
        expected = hmac.new(
            settings.STRIPE_WEBHOOK_SECRET.encode(),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, signature)
    except (ValueError, KeyError):
        return False


def _handle_event(event_type: str, data: dict):
    """Route event to appropriate handler."""
    payment_intent_id = data.get("id", "")

    if event_type == "payment_intent.succeeded":
        _handle_payment_succeeded(payment_intent_id, data)
    elif event_type == "payment_intent.payment_failed":
        _handle_payment_failed(payment_intent_id, data)
    elif event_type == "charge.refunded":
        _handle_charge_refunded(data)
    elif event_type == "charge.dispute.created":
        _handle_dispute_created(data)


def _handle_payment_succeeded(payment_intent_id: str, data: dict):
    """Handle successful payment confirmation from Stripe."""
    payment = Payment.objects.filter(processor_ref=payment_intent_id).first()
    if not payment:
        logger.warning("Payment not found for intent %s", payment_intent_id)
        return

    if payment.status == Payment.Status.COMPLETED:
        return  # Already processed

    payment.status = Payment.Status.COMPLETED
    payment.metadata["webhook_confirmation"] = data
    payment.save(update_fields=["status", "metadata"])
    logger.info("Payment %s confirmed via webhook", payment.id)


def _handle_payment_failed(payment_intent_id: str, data: dict):
    """Handle failed payment from Stripe."""
    payment = Payment.objects.filter(processor_ref=payment_intent_id).first()
    if not payment:
        return

    payment.status = Payment.Status.FAILED
    payment.metadata["failure_reason"] = data.get("last_payment_error", {}).get("message", "Unknown")
    payment.save(update_fields=["status", "metadata"])
    logger.warning("Payment %s failed: %s", payment.id, payment.metadata.get("failure_reason"))


def _handle_charge_refunded(data: dict):
    """Handle refund confirmation from Stripe."""
    payment_intent_id = data.get("payment_intent", "")
    payment = Payment.objects.filter(processor_ref=payment_intent_id).first()
    if not payment:
        return

    payment.status = Payment.Status.REFUNDED
    payment.metadata["refund_webhook"] = data
    payment.save(update_fields=["status", "metadata"])
    logger.info("Payment %s refunded via webhook", payment.id)


def _handle_dispute_created(data: dict):
    """Handle dispute creation — flag the associated account."""
    payment_intent_id = data.get("payment_intent", "")
    payment = Payment.objects.filter(processor_ref=payment_intent_id).select_related("account").first()
    if not payment:
        return

    account = payment.account
    Activity.objects.create(
        account=account,
        activity_type=Activity.ActivityType.NOTE,
        description=f"Dispute created for payment ${payment.amount}. Dispute ID: {data.get('id', 'N/A')}",
        metadata={"dispute": data, "payment_id": str(payment.id)},
    )
    logger.warning("Dispute created for payment %s on account %s", payment.id, account.id)
