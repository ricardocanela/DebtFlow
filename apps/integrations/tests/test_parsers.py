"""Tests for CSV parser and Pydantic validation."""
import os
import tempfile

import pytest

from apps.integrations.parsers import CSVParser, ImportRecordSchema


class TestImportRecordSchema:
    def test_valid_record(self):
        record = ImportRecordSchema(
            external_ref="ACC-001",
            debtor_name="John Doe",
            debtor_ssn_last4="1234",
            debtor_email="john@email.com",
            debtor_phone="555-0100",
            original_amount="1500.00",
            due_date="2024-01-15",
        )
        assert record.external_ref == "ACC-001"
        assert record.original_amount == 1500.00

    def test_missing_external_ref(self):
        with pytest.raises(Exception):
            ImportRecordSchema(
                external_ref="",
                debtor_name="John",
                original_amount="100",
            )

    def test_negative_amount(self):
        with pytest.raises(Exception):
            ImportRecordSchema(
                external_ref="ACC-001",
                debtor_name="John",
                original_amount="-100",
            )

    def test_invalid_ssn_last4(self):
        with pytest.raises(Exception):
            ImportRecordSchema(
                external_ref="ACC-001",
                debtor_name="John",
                original_amount="100",
                debtor_ssn_last4="abc",
            )

    def test_invalid_date_format(self):
        with pytest.raises(Exception):
            ImportRecordSchema(
                external_ref="ACC-001",
                debtor_name="John",
                original_amount="100",
                due_date="01/15/2024",
            )

    def test_empty_optional_fields(self):
        record = ImportRecordSchema(
            external_ref="ACC-001",
            debtor_name="John",
            original_amount="100",
        )
        assert record.debtor_email == ""
        assert record.due_date == ""


class TestCSVParser:
    def _write_csv(self, content: str) -> str:
        fd, path = tempfile.mkstemp(suffix=".csv")
        with os.fdopen(fd, "w") as f:
            f.write(content)
        return path

    def test_parse_valid_csv(self):
        csv_content = (
            "external_ref,debtor_name,debtor_ssn_last4,debtor_email,debtor_phone,original_amount,due_date,creditor_name,account_type\n"
            "ACC-001,John Doe,1234,john@email.com,555-0100,1500.00,2024-01-15,Hospital X,medical\n"
            "ACC-002,Jane Smith,5678,jane@email.com,555-0200,3200.50,2024-02-20,Bank Y,credit_card\n"
        )
        path = self._write_csv(csv_content)
        parser = CSVParser()
        records, errors = parser.parse(path)

        assert len(records) == 2
        assert len(errors) == 0
        assert records[0].external_ref == "ACC-001"
        assert records[1].original_amount == 3200.50
        os.unlink(path)

    def test_parse_csv_with_errors(self):
        csv_content = (
            "external_ref,debtor_name,debtor_ssn_last4,debtor_email,debtor_phone,original_amount,due_date,creditor_name,account_type\n"
            "ACC-001,John Doe,1234,john@email.com,555-0100,1500.00,2024-01-15,Hospital X,medical\n"
            "ACC-002,,5678,jane@email.com,555-0200,-100,invalid-date,Bank Y,credit_card\n"
        )
        path = self._write_csv(csv_content)
        parser = CSVParser()
        records, errors = parser.parse(path)

        assert len(records) == 1
        assert len(errors) == 1
        assert errors[0]["line"] == 3
        os.unlink(path)

    def test_parse_malformed_csv(self):
        """Graceful handling of malformed CSV."""
        csv_content = (
            "external_ref,debtor_name,debtor_ssn_last4,debtor_email,debtor_phone,original_amount,due_date,creditor_name,account_type\n"
            "ACC-001,John Doe,1234,john@email.com,555-0100,not_a_number,2024-01-15,Hospital X,medical\n"
        )
        path = self._write_csv(csv_content)
        parser = CSVParser()
        records, errors = parser.parse(path)

        assert len(records) == 0
        assert len(errors) == 1
        os.unlink(path)

    def test_parse_5000_records(self):
        """Performance test: parse 5000 records."""
        lines = ["external_ref,debtor_name,debtor_ssn_last4,debtor_email,debtor_phone,original_amount,due_date,creditor_name,account_type"]
        for i in range(5000):
            lines.append(f"ACC-{i:06d},Person {i},{i % 10000:04d},p{i}@email.com,555-{i:04d},{100 + i}.00,2024-01-01,Creditor,medical")
        path = self._write_csv("\n".join(lines))

        parser = CSVParser()
        records, errors = parser.parse(path)

        assert len(records) == 5000
        assert len(errors) == 0
        os.unlink(path)
