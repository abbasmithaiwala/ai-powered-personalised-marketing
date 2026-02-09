"""
Pydantic schemas for Brand API.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BrandBase(BaseModel):
    """Base brand schema with common fields."""

    name: str = Field(..., min_length=1, max_length=255, description="Brand name")
    slug: Optional[str] = Field(None, max_length=255, description="URL-friendly slug")
    cuisine_type: Optional[str] = Field(None, max_length=100, description="Primary cuisine type")
    is_active: bool = Field(True, description="Whether brand is active")


class BrandCreate(BrandBase):
    """Schema for creating a brand."""
    pass


class BrandUpdate(BaseModel):
    """Schema for updating a brand."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Brand name")
    slug: Optional[str] = Field(None, max_length=255, description="URL-friendly slug")
    cuisine_type: Optional[str] = Field(None, max_length=100, description="Primary cuisine type")
    is_active: Optional[bool] = Field(None, description="Whether brand is active")


class BrandResponse(BrandBase):
    """Schema for brand response."""

    id: UUID = Field(..., description="Brand ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class BrandListResponse(BaseModel):
    """Schema for paginated brand list response."""

    items: list[BrandResponse] = Field(..., description="List of brands")
    total: int = Field(..., description="Total number of brands")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")
