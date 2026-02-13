"""Celery tasks for report generation and export."""
import csv
import io
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def generate_account_export(user_id: int, filters: dict | None = None):
    """Generate CSV export of accounts and return the file content.

    In production, this would upload to S3 and send a download link.
    """
    from apps.accounts.models import Account

    qs = Account.objects.select_related("debtor", "agency", "assigned_to__user").all()

    if filters:
        if "status" in filters:
            qs = qs.filter(status=filters["status"])
        if "agency" in filters:
            qs = qs.filter(agency_id=filters["agency"])

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "external_ref",
        "debtor_name",
        "debtor_email",
        "agency",
        "status",
        "original_amount",
        "current_balance",
        "assigned_to",
        "due_date",
        "created_at",
    ])

    for account in qs.iterator(chunk_size=1000):
        writer.writerow([
            account.external_ref,
            account.debtor.full_name,
            account.debtor.email or "",
            account.agency.name,
            account.status,
            str(account.original_amount),
            str(account.current_balance),
            account.assigned_to.user.get_full_name() if account.assigned_to else "",
            account.due_date or "",
            account.created_at.isoformat(),
        ])

    content = output.getvalue()
    logger.info("Generated account export: %d bytes", len(content))

    # In production: upload to S3 and return URL
    return {"status": "completed", "rows": qs.count(), "size_bytes": len(content)}


@shared_task
def send_report_email(user_id: int, report_type: str, data: dict):
    """Send a report email to a user. Placeholder for email integration."""
    logger.info("Would send %s report email to user %d", report_type, user_id)
