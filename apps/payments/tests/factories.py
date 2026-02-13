"""Factory Boy factories for payments models."""
import hashlib
import time

import factory

from apps.accounts.tests.factories import AccountFactory
from apps.payments.models import Payment, PaymentProcessor


class PaymentProcessorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PaymentProcessor

    name = factory.Sequence(lambda n: f"Processor {n}")
    slug = factory.Sequence(lambda n: f"processor-{n}")
    api_base_url = "https://api.stripe.com"
    api_key_encrypted = "encrypted_test_key"
    webhook_secret = "whsec_test_secret"
    is_active = True


class PaymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Payment

    account = factory.SubFactory(AccountFactory)
    processor = factory.SubFactory(PaymentProcessorFactory)
    amount = factory.Faker("pydecimal", left_digits=3, right_digits=2, min_value=10, max_value=999)
    payment_method = Payment.Method.CARD
    status = Payment.Status.PENDING
    idempotency_key = factory.Sequence(lambda n: hashlib.sha256(f"test-key-{n}".encode()).hexdigest())
