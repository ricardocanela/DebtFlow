"""Account management models: Agency, Debtor, Account, Collector."""
import uuid

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.db import models


class Agency(models.Model):
    """Debt collection agency — the top-level tenant."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True, db_index=True)
    license_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    settings = models.JSONField(default=dict, blank=True, help_text="Customizable settings (timezone, currency, etc.)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "agencies"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Debtor(models.Model):
    """Individual or entity that owes a debt."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_ref = models.CharField(max_length=100, unique=True, db_index=True, help_text="External ID from client SFTP")
    full_name = models.CharField(max_length=255, db_index=True)
    ssn_last4 = models.CharField(max_length=4, blank=True, default="", help_text="Last 4 digits SSN (encrypted at rest)")
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    address_line1 = models.CharField(max_length=255, null=True, blank=True)
    address_city = models.CharField(max_length=100, null=True, blank=True)
    address_state = models.CharField(max_length=2, null=True, blank=True)
    address_zip = models.CharField(max_length=10, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["full_name"]
        indexes = [
            GinIndex(
                name="idx_debtor_name_trgm",
                fields=["full_name"],
                opclasses=["gin_trgm_ops"],
            ),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.external_ref})"


class Collector(models.Model):
    """Agent who works accounts within an agency."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="collector_profile")
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, related_name="collectors")
    commission_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.10)
    is_active = models.BooleanField(default=True)
    max_accounts = models.IntegerField(default=200, help_text="Simultaneous account limit")

    class Meta:
        ordering = ["user__last_name", "user__first_name"]

    def __str__(self):
        return f"{self.user.get_full_name()} @ {self.agency.name}"


class Account(models.Model):
    """A delinquent account — the primary entity in the system."""

    class Status(models.TextChoices):
        NEW = "new", "New"
        ASSIGNED = "assigned", "Assigned"
        IN_CONTACT = "in_contact", "In Contact"
        NEGOTIATING = "negotiating", "Negotiating"
        PAYMENT_PLAN = "payment_plan", "Payment Plan"
        SETTLED = "settled", "Settled"
        CLOSED = "closed", "Closed"
        DISPUTED = "disputed", "Disputed"

    # Valid status transitions (state machine)
    VALID_TRANSITIONS = {
        Status.NEW: [Status.ASSIGNED, Status.CLOSED],
        Status.ASSIGNED: [Status.IN_CONTACT, Status.CLOSED, Status.DISPUTED],
        Status.IN_CONTACT: [Status.NEGOTIATING, Status.CLOSED, Status.DISPUTED],
        Status.NEGOTIATING: [Status.PAYMENT_PLAN, Status.SETTLED, Status.CLOSED, Status.DISPUTED],
        Status.PAYMENT_PLAN: [Status.SETTLED, Status.CLOSED, Status.DISPUTED],
        Status.SETTLED: [Status.CLOSED],
        Status.CLOSED: [],
        Status.DISPUTED: [Status.IN_CONTACT, Status.CLOSED],
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, related_name="accounts")
    debtor = models.ForeignKey(Debtor, on_delete=models.PROTECT, related_name="accounts")
    assigned_to = models.ForeignKey(
        Collector, null=True, blank=True, on_delete=models.SET_NULL, related_name="accounts"
    )
    external_ref = models.CharField(max_length=100, unique=True, db_index=True, help_text="External reference from SFTP")
    original_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW, db_index=True)
    priority = models.IntegerField(default=0, db_index=True)
    due_date = models.DateField(null=True, blank=True)
    last_contact_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["agency", "status", "created_at"], name="idx_account_agency_status"),
            models.Index(fields=["agency", "assigned_to"], name="idx_account_agency_collector"),
            models.Index(
                fields=["status"],
                name="idx_account_pending",
                condition=models.Q(status__in=["new", "assigned"]),
            ),
        ]

    def __str__(self):
        return f"Account {self.external_ref} ({self.status})"

    def can_transition_to(self, new_status: str) -> bool:
        return new_status in self.VALID_TRANSITIONS.get(self.status, [])


class Activity(models.Model):
    """Timeline activity for an account (notes, status changes, etc.)."""

    class ActivityType(models.TextChoices):
        NOTE = "note", "Note"
        STATUS_CHANGE = "status_change", "Status Change"
        PAYMENT = "payment", "Payment"
        ASSIGNMENT = "assignment", "Assignment"
        IMPORT = "import", "Import"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="activities")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="activities"
    )
    activity_type = models.CharField(max_length=20, choices=ActivityType.choices)
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name_plural = "activities"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.activity_type}: {self.description[:50]}"
