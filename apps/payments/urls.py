"""URL routing for the payments app."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PaymentProcessorViewSet, PaymentViewSet
from .webhooks import stripe_webhook

router = DefaultRouter()
router.register("payments", PaymentViewSet, basename="payment")
router.register("payment-processors", PaymentProcessorViewSet, basename="payment-processor")

urlpatterns = [
    path("", include(router.urls)),
    path("payments/webhook/stripe/", stripe_webhook, name="stripe-webhook"),
]
