"""Payment models: Payment, PaymentProcessor."""
import uuid

from django.db import models


class PaymentProcessor(models.Model):
    """External payment processor configuration (e.g. Stripe)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    api_base_url = models.URLField()
    api_key_encrypted = models.TextField(help_text="API key encrypted with Fernet")
    webhook_secret = models.TextField(help_text="Webhook validation secret (encrypted)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Payment(models.Model):
    """A payment against a delinquent account."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    class Method(models.TextChoices):
        CARD = "card", "Card"
        BANK_TRANSFER = "bank_transfer", "Bank Transfer"
        CHECK = "check", "Check"
        CASH = "cash", "Cash"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(
        "accounts.Account", on_delete=models.PROTECT, related_name="payments"
    )
    processor = models.ForeignKey(
        PaymentProcessor, on_delete=models.PROTECT, related_name="payments"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=Method.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    processor_ref = models.CharField(max_length=255, unique=True, null=True, blank=True, help_text="Transaction ID at processor")
    idempotency_key = models.CharField(max_length=64, unique=True)
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional processor data")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["account", "created_at"], name="idx_payment_account_date"),
            models.Index(fields=["status", "created_at"], name="idx_payment_status_date"),
        ]

    def __str__(self):
        return f"Payment {self.id} — ${self.amount} ({self.status})"
