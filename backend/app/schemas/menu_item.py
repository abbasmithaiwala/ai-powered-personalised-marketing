"""
Pydantic schemas for MenuItem API.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer


class MenuItemBase(BaseModel):
    """Base menu item schema with common fields."""

    name: str = Field(..., min_length=1, max_length=255, description="Item name")
    description: Optional[str] = Field(None, description="Item description")
    category: Optional[str] = Field(None, max_length=100, description="Item category")
    cuisine_type: Optional[str] = Field(None, max_length=100, description="Cuisine type")
    price: Optional[Decimal] = Field(None, ge=0, description="Item price")
    dietary_tags: Optional[list[str]] = Field(None, description="Dietary tags (e.g., vegetarian, vegan)")
    flavor_tags: Optional[list[str]] = Field(None, description="Flavor tags (e.g., spicy, sweet)")
    is_available: bool = Field(True, description="Whether item is available")


class MenuItemCreate(MenuItemBase):
    """Schema for creating a menu item."""

    brand_id: UUID = Field(..., description="Brand ID")


class MenuItemUpdate(BaseModel):
    """Schema for updating a menu item."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Item name")
    description: Optional[str] = Field(None, description="Item description")
    category: Optional[str] = Field(None, max_length=100, description="Item category")
    cuisine_type: Optional[str] = Field(None, max_length=100, description="Cuisine type")
    price: Optional[Decimal] = Field(None, ge=0, description="Item price")
    dietary_tags: Optional[list[str]] = Field(None, description="Dietary tags")
    flavor_tags: Optional[list[str]] = Field(None, description="Flavor tags")
    is_available: Optional[bool] = Field(None, description="Whether item is available")


class MenuItemResponse(MenuItemBase):
    """Schema for menu item response."""

    id: UUID = Field(..., description="Menu item ID")
    brand_id: UUID = Field(..., description="Brand ID")
    embedding_id: Optional[str] = Field(None, description="Vector embedding ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    @field_serializer('price')
    def serialize_price(self, price: Optional[Decimal], _info) -> Optional[float]:
        """Serialize Decimal price as float for JSON compatibility."""
        return float(price) if price is not None else None

    class Config:
        from_attributes = True


class MenuItemListResponse(BaseModel):
    """Schema for paginated menu item list response."""

    items: list[MenuItemResponse] = Field(..., description="List of menu items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")
