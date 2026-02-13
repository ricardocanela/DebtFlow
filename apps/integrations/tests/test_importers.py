"""Tests for batch import logic."""
import os
import tempfile

import pytest

from apps.accounts.models import Account, Activity, Debtor
from apps.accounts.tests.factories import AgencyFactory
from apps.integrations.importers import BatchImporter
from apps.integrations.models import SFTPImportJob


def _write_csv(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "w") as f:
        f.write(content)
    return path


@pytest.mark.django_db
class TestBatchImporter:
    def test_import_valid_file(self):
        agency = AgencyFactory()
        job = SFTPImportJob.objects.create(agency=agency, source_host="test", file_name="test.csv")

        csv_content = (
            "external_ref,debtor_name,debtor_ssn_last4,debtor_email,debtor_phone,original_amount,due_date,creditor_name,account_type\n"
            "ACC-001,John Doe,1234,john@email.com,555-0100,1500.00,2024-01-15,Hospital X,medical\n"
            "ACC-002,Jane Smith,5678,jane@email.com,555-0200,3200.50,2024-02-20,Bank Y,credit_card\n"
        )
        path = _write_csv(csv_content)

        importer = BatchImporter(agency, job)
        result = importer.import_file(path)

        assert result.status == SFTPImportJob.Status.COMPLETED
        assert result.processed_ok == 2
        assert result.processed_errors == 0
        assert Debtor.objects.count() == 2
        assert Account.objects.count() == 2
        assert Activity.objects.filter(activity_type=Activity.ActivityType.IMPORT).count() == 2
        os.unlink(path)

    def test_import_with_errors_isolated(self):
        """Errors in one row should not block other rows."""
        agency = AgencyFactory()
        job = SFTPImportJob.objects.create(agency=agency, source_host="test", file_name="test.csv")

        csv_content = (
            "external_ref,debtor_name,debtor_ssn_last4,debtor_email,debtor_phone,original_amount,due_date,creditor_name,account_type\n"
            "ACC-001,John Doe,1234,john@email.com,555-0100,1500.00,2024-01-15,Hospital,medical\n"
            "ACC-002,,bad_ssn,invalid_email,555-0200,-100,bad-date,Bank,credit_card\n"
            "ACC-003,Bob Jones,9999,bob@email.com,555-0300,500.00,2024-03-01,Clinic,medical\n"
        )
        path = _write_csv(csv_content)

        importer = BatchImporter(agency, job)
        result = importer.import_file(path)

        assert result.processed_ok == 2  # ACC-001 and ACC-003
        assert result.processed_errors >= 1  # ACC-002 had errors
        assert Debtor.objects.count() == 2
        os.unlink(path)

    def test_upsert_existing_debtor(self):
        """Importing same external_ref should update, not duplicate."""
        agency = AgencyFactory()

        # First import
        job1 = SFTPImportJob.objects.create(agency=agency, source_host="test", file_name="test1.csv")
        csv1 = (
            "external_ref,debtor_name,debtor_ssn_last4,debtor_email,debtor_phone,original_amount,due_date,creditor_name,account_type\n"
            "ACC-001,John Doe,1234,john@email.com,555-0100,1500.00,2024-01-15,Hospital,medical\n"
        )
        path1 = _write_csv(csv1)
        BatchImporter(agency, job1).import_file(path1)

        # Second import with updated name
        job2 = SFTPImportJob.objects.create(agency=agency, source_host="test", file_name="test2.csv")
        csv2 = (
            "external_ref,debtor_name,debtor_ssn_last4,debtor_email,debtor_phone,original_amount,due_date,creditor_name,account_type\n"
            "ACC-001,John D. Doe,1234,john@email.com,555-0100,1500.00,2024-01-15,Hospital,medical\n"
        )
        path2 = _write_csv(csv2)
        BatchImporter(agency, job2).import_file(path2)

        assert Debtor.objects.count() == 1
        assert Account.objects.count() == 1
        assert Debtor.objects.first().full_name == "John D. Doe"
        os.unlink(path1)
        os.unlink(path2)
