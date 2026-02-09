"""Recommendation schemas for API requests and responses"""

from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import List


class RecommendationItem(BaseModel):
    """Single recommended menu item"""

    menu_item_id: UUID = Field(..., description="ID of the recommended menu item")
    name: str = Field(..., description="Name of the menu item")
    brand_name: str = Field(..., description="Name of the brand/restaurant")
    brand_id: UUID = Field(..., description="ID of the brand")
    category: str | None = Field(None, description="Item category")
    cuisine_type: str | None = Field(None, description="Cuisine type")
    price: float | None = Field(None, description="Item price")
    score: float = Field(..., description="Similarity score (0-1)", ge=0, le=1)
    reason: str = Field(..., description="Human-readable explanation for recommendation")


class RecommendationsResponse(BaseModel):
    """Response model for customer recommendations"""

    model_config = ConfigDict(from_attributes=True)

    customer_id: UUID = Field(..., description="Customer ID")
    items: List[RecommendationItem] = Field(..., description="List of recommended items")
    computed_at: datetime = Field(..., description="When recommendations were generated")
    fallback_used: bool = Field(
        False,
        description="True if trending items were used (no taste profile available)",
    )
