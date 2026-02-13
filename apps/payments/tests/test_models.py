"""Tests for payment models."""
import pytest

from .factories import PaymentFactory, PaymentProcessorFactory


@pytest.mark.django_db
class TestPaymentProcessor:
    def test_create_processor(self):
        processor = PaymentProcessorFactory()
        assert processor.name
        assert processor.slug
        assert processor.is_active
        assert str(processor) == processor.name


@pytest.mark.django_db
class TestPayment:
    def test_create_payment(self):
        payment = PaymentFactory()
        assert payment.amount > 0
        assert payment.idempotency_key
        assert payment.status == "pending"
        assert "$" in str(payment)

    def test_unique_idempotency_key(self):
        PaymentFactory(idempotency_key="unique-key-001")
        with pytest.raises(Exception):
            PaymentFactory(idempotency_key="unique-key-001")
