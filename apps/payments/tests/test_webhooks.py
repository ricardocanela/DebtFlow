"""Tests for Stripe webhook handler."""
import hashlib
import hmac
import json
import time

import pytest
from django.test import RequestFactory

from apps.payments.models import Payment
from apps.payments.webhooks import stripe_webhook

from .factories import PaymentFactory


def _create_stripe_signature(payload: bytes, secret: str, timestamp: int | None = None) -> str:
    """Create a valid Stripe webhook signature."""
    ts = timestamp or int(time.time())
    signed_payload = f"{ts}.".encode() + payload
    sig = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


@pytest.mark.django_db
class TestStripeWebhook:
    def test_valid_signature_accepted(self, settings):
        settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        payload = json.dumps({
            "id": "evt_test_001",
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_test_001"}},
        }).encode()

        factory = RequestFactory()
        request = factory.post(
            "/api/v1/payments/webhook/stripe/",
            data=payload,
            content_type="application/json",
        )
        request.META["HTTP_STRIPE_SIGNATURE"] = _create_stripe_signature(payload, "whsec_test")

        response = stripe_webhook(request)
        assert response.status_code == 200

    def test_invalid_signature_rejected(self, settings):
        settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        payload = json.dumps({"id": "evt_test", "type": "payment_intent.succeeded"}).encode()

        factory = RequestFactory()
        request = factory.post(
            "/api/v1/payments/webhook/stripe/",
            data=payload,
            content_type="application/json",
        )
        request.META["HTTP_STRIPE_SIGNATURE"] = "t=123,v1=invalidsig"

        response = stripe_webhook(request)
        assert response.status_code == 400

    def test_missing_signature_rejected(self, settings):
        settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        payload = json.dumps({"id": "evt_test"}).encode()

        factory = RequestFactory()
        request = factory.post(
            "/api/v1/payments/webhook/stripe/",
            data=payload,
            content_type="application/json",
        )

        response = stripe_webhook(request)
        assert response.status_code == 400

    def test_duplicate_event_idempotency(self, settings):
        """Same event ID should be processed only once."""
        settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        event_id = "evt_idempotent_001"
        payload = json.dumps({
            "id": event_id,
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_test"}},
        }).encode()

        factory = RequestFactory()
        sig = _create_stripe_signature(payload, "whsec_test")

        # First request
        request1 = factory.post("/api/v1/payments/webhook/stripe/", data=payload, content_type="application/json")
        request1.META["HTTP_STRIPE_SIGNATURE"] = sig
        response1 = stripe_webhook(request1)
        assert response1.status_code == 200

        # Second request (same event) — should return already_processed
        request2 = factory.post("/api/v1/payments/webhook/stripe/", data=payload, content_type="application/json")
        request2.META["HTTP_STRIPE_SIGNATURE"] = sig
        response2 = stripe_webhook(request2)
        assert response2.status_code == 200
        assert json.loads(response2.content)["status"] == "already_processed"

    def test_payment_status_updated_on_success(self, settings):
        """Webhook should update payment status to completed."""
        settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        payment = PaymentFactory(processor_ref="pi_webhook_test", status=Payment.Status.PENDING)

        payload = json.dumps({
            "id": "evt_success_001",
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_webhook_test"}},
        }).encode()

        factory = RequestFactory()
        request = factory.post("/api/v1/payments/webhook/stripe/", data=payload, content_type="application/json")
        request.META["HTTP_STRIPE_SIGNATURE"] = _create_stripe_signature(payload, "whsec_test")

        response = stripe_webhook(request)
        assert response.status_code == 200

        payment.refresh_from_db()
        assert payment.status == Payment.Status.COMPLETED
