"""Integration tests for payments API endpoints."""
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from rest_framework import status

from apps.accounts.tests.factories import AccountFactory
from apps.payments.models import Payment

from .factories import PaymentFactory, PaymentProcessorFactory


@pytest.mark.django_db
class TestPaymentListAPI:
    def test_list_payments(self, authenticated_admin_client):
        PaymentFactory.create_batch(3)
        response = authenticated_admin_client.get("/api/v1/payments/")
        assert response.status_code == status.HTTP_200_OK

    def test_list_payments_unauthenticated(self, api_client):
        response = api_client.get("/api/v1/payments/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestPaymentDetailAPI:
    def test_retrieve_payment(self, authenticated_admin_client):
        payment = PaymentFactory()
        response = authenticated_admin_client.get(f"/api/v1/payments/{payment.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert str(response.data["id"]) == str(payment.id)

    def test_retrieve_includes_processor_name(self, authenticated_admin_client):
        processor = PaymentProcessorFactory(name="Stripe Test")
        payment = PaymentFactory(processor=processor)
        response = authenticated_admin_client.get(f"/api/v1/payments/{payment.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["processor_name"] == "Stripe Test"


@pytest.mark.django_db
class TestPaymentCreateAPI:
    @patch("apps.payments.services.stripe")
    def test_create_payment(self, mock_stripe, authenticated_admin_client):
        mock_intent = MagicMock()
        mock_intent.id = "pi_test_123"
        mock_intent.status = "succeeded"
        mock_intent.client_secret = "secret"
        mock_stripe.PaymentIntent.create.return_value = mock_intent

        account = AccountFactory()
        processor = PaymentProcessorFactory()

        response = authenticated_admin_client.post("/api/v1/payments/", {
            "account": str(account.id),
            "processor": str(processor.id),
            "amount": "250.00",
            "payment_method": "card",
        })
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_payment_negative_amount_rejected(self, authenticated_admin_client):
        account = AccountFactory()
        processor = PaymentProcessorFactory()

        response = authenticated_admin_client.post("/api/v1/payments/", {
            "account": str(account.id),
            "processor": str(processor.id),
            "amount": "-100.00",
            "payment_method": "card",
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestPaymentRefundAPI:
    def test_refund_non_completed_payment_rejected(self, authenticated_admin_client):
        payment = PaymentFactory(status=Payment.Status.PENDING)
        response = authenticated_admin_client.post(f"/api/v1/payments/{payment.id}/refund/", {
            "reason": "Test refund",
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("apps.payments.services.stripe")
    def test_refund_completed_payment(self, mock_stripe, authenticated_admin_client):
        mock_refund = MagicMock()
        mock_refund.id = "re_test_123"
        mock_refund.status = "succeeded"
        mock_stripe.Refund.create.return_value = mock_refund

        payment = PaymentFactory(
            status=Payment.Status.COMPLETED,
            processor_ref="pi_refund_test",
        )
        response = authenticated_admin_client.post(f"/api/v1/payments/{payment.id}/refund/", {
            "reason": "Customer requested",
        })
        assert response.status_code == status.HTTP_200_OK
        payment.refresh_from_db()
        assert payment.status == Payment.Status.REFUNDED
