"""Batch import logic for SFTP-ingested records."""
import logging
from datetime import date

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Account, Activity, Agency, Debtor

from .models import SFTPImportJob
from .parsers import CSVParser, ImportRecordSchema

logger = logging.getLogger(__name__)

BATCH_SIZE = 1000


class BatchImporter:
    """Imports validated CSV records into Account/Debtor tables.

    - Processes in batches of 1000 within transactions
    - Upserts Debtors by external_ref
    - Creates/updates Accounts by external_ref
    - Errors are isolated per row (one bad record doesn't block the batch)
    """

    def __init__(self, agency: Agency, import_job: SFTPImportJob):
        self.agency = agency
        self.import_job = import_job

    def import_file(self, file_path: str) -> SFTPImportJob:
        """Parse and import a CSV file."""
        self.import_job.status = SFTPImportJob.Status.PROCESSING
        self.import_job.started_at = timezone.now()
        self.import_job.save(update_fields=["status", "started_at"])

        parser = CSVParser()
        valid_records, parse_errors = parser.parse(file_path)

        self.import_job.total_records = len(valid_records) + len(parse_errors)
        self.import_job.processed_errors = len(parse_errors)
        self.import_job.error_details = parse_errors
        self.import_job.save(update_fields=["total_records", "processed_errors", "error_details"])

        # Process in batches
        processed_ok = 0
        for i in range(0, len(valid_records), BATCH_SIZE):
            batch = valid_records[i : i + BATCH_SIZE]
            ok_count, batch_errors = self._process_batch(batch, start_line=i + 2 + len(parse_errors))
            processed_ok += ok_count
            if batch_errors:
                self.import_job.error_details.extend(batch_errors)
                self.import_job.processed_errors += len(batch_errors)

        self.import_job.processed_ok = processed_ok
        self.import_job.status = (
            SFTPImportJob.Status.COMPLETED if self.import_job.processed_errors == 0 else SFTPImportJob.Status.FAILED
        )
        self.import_job.completed_at = timezone.now()
        self.import_job.save()

        logger.info(
            "Import job %s completed: %d OK, %d errors out of %d total",
            self.import_job.id,
            processed_ok,
            self.import_job.processed_errors,
            self.import_job.total_records,
        )
        return self.import_job

    def _process_batch(self, records: list[ImportRecordSchema], start_line: int) -> tuple[int, list[dict]]:
        """Process a batch of records within a transaction. Errors isolated per row."""
        ok_count = 0
        errors = []

        for idx, record in enumerate(records):
            try:
                with transaction.atomic():
                    self._upsert_record(record)
                    ok_count += 1
            except Exception as e:
                errors.append(
                    {
                        "line": start_line + idx,
                        "error": str(e),
                        "data": record.model_dump(),
                    }
                )

        return ok_count, errors

    def _upsert_record(self, record: ImportRecordSchema):
        """Upsert a single debtor + account from a validated record."""
        # Upsert Debtor
        debtor, _ = Debtor.objects.update_or_create(
            external_ref=record.external_ref,
            defaults={
                "full_name": record.debtor_name,
                "ssn_last4": record.debtor_ssn_last4,
                "email": record.debtor_email or None,
                "phone": record.debtor_phone or None,
            },
        )

        # Upsert Account
        due_date = date.fromisoformat(record.due_date) if record.due_date else None
        account, created = Account.objects.update_or_create(
            external_ref=record.external_ref,
            defaults={
                "agency": self.agency,
                "debtor": debtor,
                "original_amount": record.original_amount,
                "current_balance": record.original_amount,
                "due_date": due_date,
            },
        )

        if created:
            Activity.objects.create(
                account=account,
                activity_type=Activity.ActivityType.IMPORT,
                description=f"Account imported from SFTP file {self.import_job.file_name}",
                metadata={"import_job_id": str(self.import_job.id)},
            )
