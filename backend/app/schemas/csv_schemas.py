"""
Pydantic models for CSV row validation.

Defines the expected structure for order CSV rows with validation rules.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class OrderCSVRow(BaseModel):
    """
    Validated order CSV row.

    All fields are converted to appropriate types with validation.
    """

    # Required fields
    order_id: str = Field(..., min_length=1, max_length=255)
    customer_email: str = Field(..., min_length=3, max_length=255)
    brand_name: str = Field(..., min_length=1, max_length=255)
    item_name: str = Field(..., min_length=1, max_length=500)
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    order_date: datetime

    # Optional fields
    customer_id: Optional[str] = Field(None, max_length=255)
    customer_name: Optional[str] = Field(None, max_length=255)
    customer_first_name: Optional[str] = Field(None, max_length=100)
    customer_last_name: Optional[str] = Field(None, max_length=100)
    customer_phone: Optional[str] = Field(None, max_length=50)
    customer_city: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    order_total: Optional[Decimal] = Field(None, ge=0)
    order_channel: Optional[str] = Field(None, max_length=50)

    # Internal tracking
    row_number: int = Field(..., description="Original CSV row number for error reporting")

    model_config = {
        "str_strip_whitespace": True,
        "validate_assignment": True,
    }

    @field_validator("customer_email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Basic email validation."""
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email format")
        return v.lower()

    @field_validator("quantity", mode="before")
    @classmethod
    def validate_quantity(cls, v) -> int:
        """Parse quantity from various formats."""
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            # Remove common non-numeric characters
            cleaned = v.strip().replace(",", "")
            try:
                qty = int(float(cleaned))
                if qty <= 0:
                    raise ValueError("Quantity must be positive")
                return qty
            except (ValueError, TypeError):
                raise ValueError(f"Invalid quantity: {v}")
        try:
            return int(v)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid quantity: {v}")

    @field_validator("unit_price", "order_total", mode="before")
    @classmethod
    def validate_price(cls, v) -> Decimal | None:
        """Parse price from various formats, handling currency symbols."""
        if v is None or v == "":
            return None

        if isinstance(v, (Decimal, int, float)):
            return Decimal(str(v))

        if isinstance(v, str):
            # Remove currency symbols and whitespace
            cleaned = v.strip()

            # Remove common currency symbols
            for symbol in ["£", "$", "€", "AED", "₹", "¥"]:
                cleaned = cleaned.replace(symbol, "")

            # Remove thousands separators
            cleaned = cleaned.replace(",", "")

            # Handle empty string after cleaning
            if not cleaned:
                return None

            try:
                price = Decimal(cleaned)
                if price < 0:
                    raise ValueError("Price cannot be negative")
                return price
            except (ValueError, TypeError):
                raise ValueError(f"Invalid price: {v}")

        raise ValueError(f"Invalid price type: {type(v)}")

    @field_validator("order_date", mode="before")
    @classmethod
    def validate_date(cls, v) -> datetime:
        """Parse date from various formats."""
        if isinstance(v, datetime):
            return v

        if isinstance(v, str):
            v = v.strip()

            # Try common date formats
            formats = [
                # ISO 8601
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%d",
                # DD/MM/YYYY
                "%d/%m/%Y %H:%M:%S",
                "%d/%m/%Y %H:%M",
                "%d/%m/%Y",
                # MM/DD/YYYY
                "%m/%d/%Y %H:%M:%S",
                "%m/%d/%Y %H:%M",
                "%m/%d/%Y",
                # DD-MM-YYYY
                "%d-%m-%Y %H:%M:%S",
                "%d-%m-%Y %H:%M",
                "%d-%m-%Y",
                # YYYY/MM/DD
                "%Y/%m/%d %H:%M:%S",
                "%Y/%m/%d %H:%M",
                "%Y/%m/%d",
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(v, fmt)
                except ValueError:
                    continue

            # Try Unix timestamp (seconds)
            try:
                timestamp = float(v)
                return datetime.fromtimestamp(timestamp)
            except (ValueError, TypeError, OSError):
                pass

            raise ValueError(f"Could not parse date: {v}")

        raise ValueError(f"Invalid date type: {type(v)}")

    @model_validator(mode="after")
    def validate_customer_name(self) -> "OrderCSVRow":
        """
        Ensure we have customer name information.

        If customer_name is provided but not first/last, split it.
        """
        if self.customer_name and not (self.customer_first_name or self.customer_last_name):
            parts = self.customer_name.split(None, 1)
            if len(parts) == 2:
                self.customer_first_name = parts[0]
                self.customer_last_name = parts[1]
            elif len(parts) == 1:
                self.customer_first_name = parts[0]

        return self


class ValidationError(BaseModel):
    """Individual validation error for a CSV row."""

    row: int = Field(..., description="Row number in CSV (1-indexed)")
    field: str = Field(..., description="Field name that failed validation")
    error: str = Field(..., description="Error message")
    value: Optional[str] = Field(None, description="Invalid value that caused error")


class CSVValidationResult(BaseModel):
    """Result of CSV validation."""

    valid: bool = Field(..., description="Whether CSV is valid overall")
    total_rows: int = Field(..., description="Total data rows in CSV (excluding header)")
    valid_rows: int = Field(..., description="Number of valid rows")
    invalid_rows: int = Field(..., description="Number of invalid rows")
    errors: list[ValidationError] = Field(default_factory=list, description="List of validation errors")
    missing_columns: list[str] = Field(default_factory=list, description="Required columns that are missing")
    column_mapping: dict[str, str] = Field(
        default_factory=dict, description="Mapping of CSV headers to canonical field names"
    )

    @property
    def has_missing_columns(self) -> bool:
        """Check if required columns are missing."""
        return len(self.missing_columns) > 0

    @property
    def error_summary(self) -> str:
        """Generate human-readable error summary."""
        if self.valid:
            return "CSV is valid"

        issues = []
        if self.missing_columns:
            issues.append(f"Missing required columns: {', '.join(self.missing_columns)}")
        if self.invalid_rows > 0:
            issues.append(f"{self.invalid_rows} row(s) with validation errors")

        return "; ".join(issues)
