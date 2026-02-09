"""
CSV validation service.

Handles CSV parsing, column detection, and row-by-row validation.
"""

import csv
import io
from typing import Any, Dict, List, TextIO

from app.core.csv_mappings import (
    REQUIRED_FIELDS,
    get_canonical_field_name,
    normalize_header,
)
from app.schemas.csv_schemas import (
    CSVValidationResult,
    OrderCSVRow,
    ValidationError,
)


class CSVValidator:
    """
    CSV validation service with flexible column mapping.

    Handles header detection, column mapping, and row-by-row validation.
    """

    def __init__(self):
        """Initialize CSV validator."""
        pass

    def detect_columns(self, headers: List[str]) -> Dict[str, str]:
        """
        Detect and map CSV headers to canonical field names.

        Args:
            headers: List of CSV header strings

        Returns:
            Dictionary mapping canonical field names to actual CSV headers
        """
        column_mapping: Dict[str, str] = {}

        for header in headers:
            canonical = get_canonical_field_name(header)
            if canonical:
                # Map canonical name to actual CSV header
                column_mapping[canonical] = header

        return column_mapping

    def check_required_columns(self, column_mapping: Dict[str, str]) -> List[str]:
        """
        Check if all required columns are present.

        Args:
            column_mapping: Dictionary of canonical -> CSV header mappings

        Returns:
            List of missing required field names
        """
        mapped_fields = set(column_mapping.keys())
        required_set = set(REQUIRED_FIELDS)
        missing = required_set - mapped_fields

        return sorted(list(missing))

    def validate_csv_file(
        self,
        file_content: str | TextIO,
        max_errors: int = 1000,
    ) -> CSVValidationResult:
        """
        Validate an entire CSV file.

        Args:
            file_content: CSV content as string or file-like object
            max_errors: Maximum number of errors to collect (prevents memory issues)

        Returns:
            CSVValidationResult with validation status and errors
        """
        # Handle string or file-like input
        if isinstance(file_content, str):
            file_obj = io.StringIO(file_content)
        else:
            file_obj = file_content

        # Read CSV
        try:
            reader = csv.DictReader(file_obj)

            # Get headers
            headers = reader.fieldnames
            if not headers:
                return CSVValidationResult(
                    valid=False,
                    total_rows=0,
                    valid_rows=0,
                    invalid_rows=0,
                    errors=[
                        ValidationError(
                            row=0,
                            field="headers",
                            error="CSV file has no headers",
                        )
                    ],
                )

            # Detect columns
            column_mapping = self.detect_columns(headers)

            # Check for missing required columns
            missing_columns = self.check_required_columns(column_mapping)
            if missing_columns:
                # Create reverse mapping for display
                reverse_mapping = {v: k for k, v in column_mapping.items()}

                return CSVValidationResult(
                    valid=False,
                    total_rows=0,
                    valid_rows=0,
                    invalid_rows=0,
                    missing_columns=missing_columns,
                    column_mapping=reverse_mapping,
                    errors=[
                        ValidationError(
                            row=0,
                            field="required_columns",
                            error=f"Missing required columns: {', '.join(missing_columns)}",
                        )
                    ],
                )

            # Validate rows
            errors: List[ValidationError] = []
            valid_rows = 0
            total_rows = 0

            for row_idx, row in enumerate(reader, start=1):
                total_rows += 1

                # Skip empty rows
                if not any(row.values()):
                    continue

                # Map row data to canonical field names
                mapped_row = {}
                for canonical, csv_header in column_mapping.items():
                    mapped_row[canonical] = row.get(csv_header)

                # Add row number for error reporting
                mapped_row["row_number"] = row_idx

                # Validate row
                try:
                    OrderCSVRow.model_validate(mapped_row)
                    valid_rows += 1
                except Exception as e:
                    # Parse validation error
                    if hasattr(e, "errors"):
                        # Pydantic validation error
                        for error in e.errors():
                            field = error["loc"][0] if error["loc"] else "unknown"
                            field_str = str(field)

                            # Get error message
                            msg = error.get("msg", str(error))

                            # Handle context for better error messages
                            if "ctx" in error and "error" in error["ctx"]:
                                ctx_error = error["ctx"]["error"]
                                if hasattr(ctx_error, "__str__"):
                                    msg = str(ctx_error)

                            # Extract value if available
                            value = mapped_row.get(field_str)
                            value_str = str(value)[:100] if value is not None else None

                            errors.append(
                                ValidationError(
                                    row=row_idx,
                                    field=field_str,
                                    error=msg,
                                    value=value_str,
                                )
                            )
                    else:
                        # Generic error
                        errors.append(
                            ValidationError(
                                row=row_idx,
                                field="unknown",
                                error=str(e),
                            )
                        )

                # Stop collecting errors if we hit max
                if len(errors) >= max_errors:
                    errors.append(
                        ValidationError(
                            row=0,
                            field="max_errors",
                            error=f"Maximum error limit ({max_errors}) reached. Additional errors not shown.",
                        )
                    )
                    break

            invalid_rows = total_rows - valid_rows

            # Create reverse mapping for display (CSV header -> canonical name)
            reverse_mapping = {v: k for k, v in column_mapping.items()}

            return CSVValidationResult(
                valid=valid_rows == total_rows and total_rows > 0,
                total_rows=total_rows,
                valid_rows=valid_rows,
                invalid_rows=invalid_rows,
                errors=errors,
                column_mapping=reverse_mapping,
            )

        except csv.Error as e:
            return CSVValidationResult(
                valid=False,
                total_rows=0,
                valid_rows=0,
                invalid_rows=0,
                errors=[
                    ValidationError(
                        row=0,
                        field="csv_parse",
                        error=f"CSV parsing error: {str(e)}",
                    )
                ],
            )
        except Exception as e:
            return CSVValidationResult(
                valid=False,
                total_rows=0,
                valid_rows=0,
                invalid_rows=0,
                errors=[
                    ValidationError(
                        row=0,
                        field="unexpected",
                        error=f"Unexpected error: {str(e)}",
                    )
                ],
            )

    def parse_valid_rows(
        self,
        file_content: str | TextIO,
    ) -> List[OrderCSVRow]:
        """
        Parse and return only valid rows from CSV.

        Invalid rows are silently skipped. Use validate_csv_file() first
        to get detailed validation errors.

        Args:
            file_content: CSV content as string or file-like object

        Returns:
            List of validated OrderCSVRow objects
        """
        # Handle string or file-like input
        if isinstance(file_content, str):
            file_obj = io.StringIO(file_content)
        else:
            file_obj = file_content

        valid_rows: List[OrderCSVRow] = []

        try:
            reader = csv.DictReader(file_obj)
            headers = reader.fieldnames

            if not headers:
                return []

            # Detect columns
            column_mapping = self.detect_columns(headers)

            # Check required columns present
            if self.check_required_columns(column_mapping):
                return []

            # Parse rows
            for row_idx, row in enumerate(reader, start=1):
                # Skip empty rows
                if not any(row.values()):
                    continue

                # Map row data
                mapped_row = {}
                for canonical, csv_header in column_mapping.items():
                    mapped_row[canonical] = row.get(csv_header)

                mapped_row["row_number"] = row_idx

                # Validate and collect
                try:
                    validated_row = OrderCSVRow.model_validate(mapped_row)
                    valid_rows.append(validated_row)
                except Exception:
                    # Skip invalid rows
                    continue

        except Exception:
            # Return what we have so far
            pass

        return valid_rows
