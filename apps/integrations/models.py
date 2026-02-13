"""SFTP integration models."""
import uuid

from django.db import models


class SFTPImportJob(models.Model):
    """Tracks an SFTP file import job."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agency = models.ForeignKey("accounts.Agency", on_delete=models.CASCADE, related_name="import_jobs")
    source_host = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255)
    file_path_s3 = models.CharField(max_length=500, null=True, blank=True, help_text="S3 path after upload")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    total_records = models.IntegerField(default=0)
    processed_ok = models.IntegerField(default=0)
    processed_errors = models.IntegerField(default=0)
    error_details = models.JSONField(default=list, blank=True, help_text="Error list by line number")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "SFTP Import Job"
        verbose_name_plural = "SFTP Import Jobs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["agency", "status", "created_at"], name="idx_import_agency_status"),
        ]

    def __str__(self):
        return f"Import {self.file_name} ({self.status})"
