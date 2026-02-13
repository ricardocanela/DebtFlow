"""CSV parser with Pydantic validation for SFTP imports."""
import csv
import logging
from decimal import Decimal, InvalidOperation
from typing import Any

from pydantic import BaseModel, EmailStr, field_validator

logger = logging.getLogger(__name__)


class ImportRecordSchema(BaseModel):
    """Pydantic schema for validating each CSV row."""

    external_ref: str
    debtor_name: str
    debtor_ssn_last4: str = ""
    debtor_email: str = ""
    debtor_phone: str = ""
    original_amount: Decimal
    due_date: str = ""
    creditor_name: str = ""
    account_type: str = ""

    @field_validator("external_ref")
    @classmethod
    def external_ref_valid(cls, v: str) -> str:
        if not v or len(v) > 100:
            raise ValueError("external_ref is required and must be <= 100 chars")
        return v.strip()

    @field_validator("debtor_name")
    @classmethod
    def debtor_name_valid(cls, v: str) -> str:
        if not v:
            raise ValueError("debtor_name is required")
        return v.strip()

    @field_validator("original_amount", mode="before")
    @classmethod
    def amount_positive(cls, v: Any) -> Decimal:
        try:
            d = Decimal(str(v))
        except (InvalidOperation, TypeError):
            raise ValueError("original_amount must be a valid decimal")
        if d <= 0:
            raise ValueError("original_amount must be positive")
        return d

    @field_validator("debtor_ssn_last4")
    @classmethod
    def ssn_last4_valid(cls, v: str) -> str:
        if v and (len(v) != 4 or not v.isdigit()):
            raise ValueError("debtor_ssn_last4 must be exactly 4 digits")
        return v

    @field_validator("debtor_email")
    @classmethod
    def email_valid(cls, v: str) -> str:
        if v and "@" not in v:
            raise ValueError("Invalid email format")
        return v.strip()

    @field_validator("due_date")
    @classmethod
    def due_date_format(cls, v: str) -> str:
        if v:
            import re

            if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
                raise ValueError("due_date must be in YYYY-MM-DD format")
        return v


class CSVParser:
    """Parses CSV files and validates each row with Pydantic."""

    EXPECTED_HEADERS = {
        "external_ref",
        "debtor_name",
        "debtor_ssn_last4",
        "debtor_email",
        "debtor_phone",
        "original_amount",
        "due_date",
        "creditor_name",
        "account_type",
    }

    def parse(self, file_path: str) -> tuple[list[ImportRecordSchema], list[dict]]:
        """Parse a CSV file. Returns (valid_records, errors).

        Errors contain line number and reason for each invalid row.
        """
        valid_records = []
        errors = []

        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            # Validate headers
            if reader.fieldnames:
                missing = self.EXPECTED_HEADERS - set(reader.fieldnames)
                extra_required = {"external_ref", "debtor_name", "original_amount"}
                missing_required = missing & extra_required
                if missing_required:
                    errors.append(
                        {"line": 1, "error": f"Missing required columns: {missing_required}", "data": {}}
                    )
                    return [], errors

            for line_num, row in enumerate(reader, start=2):
                try:
                    record = ImportRecordSchema(**row)
                    valid_records.append(record)
                except Exception as e:
                    errors.append(
                        {
                            "line": line_num,
                            "error": str(e),
                            "data": dict(row),
                        }
                    )

        logger.info("Parsed %d valid records, %d errors from %s", len(valid_records), len(errors), file_path)
        return valid_records, errors
