"""Celery configuration for DebtFlow."""
import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("debtflow")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
app.conf.include = [
    "tasks.sftp_tasks",
    "tasks.payment_tasks",
    "tasks.report_tasks",
    "tasks.maintenance",
]

app.conf.beat_schedule = {
    "sftp-poll-all-agencies": {
        "task": "tasks.sftp_tasks.sftp_poll_all_agencies",
        "schedule": 900.0,  # every 15 minutes
    },
    "reconcile-pending-payments": {
        "task": "tasks.payment_tasks.reconcile_payments",
        "schedule": 3600.0,  # every hour
    },
    "vacuum-large-tables": {
        "task": "tasks.maintenance.vacuum_tables",
        "schedule": crontab(hour=3, minute=0, day_of_week="sunday"),
    },
    "archive-old-audit-logs": {
        "task": "tasks.maintenance.archive_audit_logs",
        "schedule": crontab(hour=2, minute=0, day_of_month="1"),
    },
}
