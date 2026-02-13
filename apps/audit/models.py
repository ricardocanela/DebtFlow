"""Audit trail model with monthly partitioning support."""
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class AuditLog(models.Model):
    """Immutable audit log — records all data changes in the system.

    Designed for monthly RANGE partitioning on created_at.
    Retention: 24 months online, then archive to S3.
    """

    class Action(models.TextChoices):
        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"
        VIEW = "view", "View"
        EXPORT = "export", "Export"
        WEBHOOK_RECEIVED = "webhook_received", "Webhook Received"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField(db_index=True)
    content_object = GenericForeignKey("content_type", "object_id")
    changes = models.JSONField(default=dict, blank=True, help_text="Diff of changes (old/new values)")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["content_type", "object_id", "created_at"],
                name="idx_audit_object_timeline",
            ),
        ]

    def __str__(self):
        return f"{self.action} on {self.content_type} #{self.object_id}"
