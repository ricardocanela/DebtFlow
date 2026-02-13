"""Celery tasks for database maintenance and cleanup."""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def vacuum_tables():
    """Run VACUUM ANALYZE on large tables.

    Runs weekly via Celery Beat (Sunday 3 AM).
    """
    from django.db import connection

    tables = [
        "accounts_account",
        "accounts_activity",
        "payments_payment",
        "audit_auditlog",
    ]

    with connection.cursor() as cursor:
        for table in tables:
            try:
                cursor.execute(f"VACUUM ANALYZE {table}")  # noqa: S608
                logger.info("VACUUM ANALYZE completed for %s", table)
            except Exception:
                logger.exception("VACUUM ANALYZE failed for %s", table)


@shared_task
def archive_audit_logs():
    """Archive audit logs older than 24 months.

    Runs monthly via Celery Beat (1st of month, 2 AM).
    In production, this would export to S3 before deleting.
    """
    from datetime import timedelta

    from django.utils import timezone

    from apps.audit.models import AuditLog

    cutoff = timezone.now() - timedelta(days=730)  # ~24 months
    old_logs = AuditLog.objects.filter(created_at__lt=cutoff)
    count = old_logs.count()

    if count > 0:
        # In production: export to S3 first
        logger.info("Archiving %d audit logs older than %s", count, cutoff.isoformat())
        old_logs.delete()
        logger.info("Archived (deleted) %d audit logs", count)
    else:
        logger.info("No audit logs to archive")
