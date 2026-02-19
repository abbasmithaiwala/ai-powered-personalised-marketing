"""Schemas for PDF menu import workflow."""
from decimal import Decimal, InvalidOperation
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.menu_item import MenuItemResponse


class ParsedMenuItem(BaseModel):
    """
    A single menu item extracted by OCR from a PDF.
    Ephemeral — used only for the review stage before bulk insert.
    """

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    cuisine_type: Optional[str] = Field(None, max_length=100)
    price: Optional[Decimal] = Field(None, ge=0)
    dietary_tags: list[str] = Field(default_factory=list)
    flavor_tags: list[str] = Field(default_factory=list)

    @field_validator("price", mode="before")
    @classmethod
    def coerce_price(cls, v: object) -> Optional[Decimal]:
        """Accept int, float, str representations of price; treat N/A / empty as None."""
        if v is None or v == "" or (isinstance(v, str) and v.strip().upper() in ("N/A", "NA", "-")):
            return None
        try:
            return Decimal(str(v))
        except (InvalidOperation, TypeError):
            return None

    @field_validator("dietary_tags", "flavor_tags", mode="before")
    @classmethod
    def coerce_tags(cls, v: object) -> list[str]:
        """Ensure tags is always a list of non-empty strings."""
        if v is None:
            return []
        if isinstance(v, str):
            # Support comma-separated string from OCR
            return [t.strip() for t in v.split(",") if t.strip()]
        if isinstance(v, list):
            return [str(t).strip() for t in v if str(t).strip()]
        return []


class PDFParseResponse(BaseModel):
    """Response from POST /menu-items/parse-pdf."""

    items: list[ParsedMenuItem]
    count: int
    filename: str


class BulkCreateRequest(BaseModel):
    """Request body for POST /menu-items/bulk-create."""

    brand_id: UUID
    items: list[ParsedMenuItem] = Field(..., min_length=1, max_length=200)


class BulkCreateResponse(BaseModel):
    """Response from POST /menu-items/bulk-create."""

    created: int
    failed: int
    items: list[MenuItemResponse]
