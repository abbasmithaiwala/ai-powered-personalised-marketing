"""Pydantic schemas for campaign management"""

from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, List


# ============================================================================
# Segment Filter Schemas
# ============================================================================


class SegmentFilters(BaseModel):
    """
    Filter criteria for customer segmentation.

    These filters are used to select campaign recipients.
    """

    last_order_after: Optional[datetime] = Field(
        None, description="Include customers who ordered after this date"
    )
    last_order_before: Optional[datetime] = Field(
        None, description="Include customers who ordered before this date"
    )
    total_spend_min: Optional[float] = Field(
        None, ge=0, description="Minimum total spend"
    )
    total_spend_max: Optional[float] = Field(
        None, ge=0, description="Maximum total spend"
    )
    total_orders_min: Optional[int] = Field(
        None, ge=0, description="Minimum number of orders"
    )
    favorite_cuisine: Optional[str] = Field(
        None, description="Filter by favorite cuisine type"
    )
    dietary_flag: Optional[str] = Field(
        None, description="Filter by dietary flag (vegetarian | vegan | halal | gluten_free)"
    )
    city: Optional[str] = Field(None, description="Filter by customer city")
    order_frequency: Optional[str] = Field(
        None, description="Filter by order frequency (daily | weekly | monthly | occasional)"
    )
    brand_id: Optional[UUID] = Field(
        None, description="Filter by customers who ordered from this brand"
    )

    @field_validator("dietary_flag")
    @classmethod
    def validate_dietary_flag(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed = {"vegetarian", "vegan", "halal", "gluten_free"}
            if v not in allowed:
                raise ValueError(f"dietary_flag must be one of {allowed}")
        return v

    @field_validator("order_frequency")
    @classmethod
    def validate_order_frequency(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed = {"daily", "weekly", "monthly", "occasional"}
            if v not in allowed:
                raise ValueError(f"order_frequency must be one of {allowed}")
        return v


# ============================================================================
# Campaign Schemas
# ============================================================================


class CampaignBase(BaseModel):
    """Base campaign schema with common fields"""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    purpose: Optional[str] = Field(
        None, description="Campaign purpose used in message generation prompt"
    )
    segment_filters: Optional[SegmentFilters] = Field(
        None, description="Filter criteria for selecting recipients"
    )


class CampaignCreate(CampaignBase):
    """Schema for creating a new campaign"""

    pass


class CampaignUpdate(BaseModel):
    """Schema for updating a campaign (only draft campaigns can be updated)"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    purpose: Optional[str] = None
    segment_filters: Optional[SegmentFilters] = None


class CampaignResponse(CampaignBase):
    """Schema for campaign response"""

    id: UUID
    status: str = Field(
        ..., description="draft | previewing | ready | executing | completed | failed"
    )
    total_recipients: int
    generated_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CampaignListResponse(BaseModel):
    """Schema for paginated list of campaigns"""

    items: List[CampaignResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================================================
# Campaign Recipient Schemas
# ============================================================================


class CampaignRecipientResponse(BaseModel):
    """Schema for campaign recipient response"""

    id: UUID
    campaign_id: UUID
    customer_id: UUID
    customer_email: Optional[str] = None
    customer_name: Optional[str] = None
    generated_message: Optional[Dict[str, Any]] = None
    status: str = Field(..., description="pending | generated | failed")
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CampaignRecipientListResponse(BaseModel):
    """Schema for paginated list of campaign recipients"""

    items: List[CampaignRecipientResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================================================
# Campaign Execution Schemas
# ============================================================================


class CampaignPreviewRequest(BaseModel):
    """Request to preview campaign messages"""

    sample_size: int = Field(3, ge=1, le=10, description="Number of sample messages to generate")


class CampaignPreviewResponse(BaseModel):
    """Response with preview of campaign messages"""

    campaign_id: UUID
    sample_messages: List[CampaignRecipientResponse]
    estimated_audience_size: int


class CampaignExecuteResponse(BaseModel):
    """Response when campaign execution starts"""

    campaign_id: UUID
    status: str
    total_recipients: int
    message: str


# ============================================================================
# Audience Count Schema
# ============================================================================


class AudienceCountRequest(BaseModel):
    """Request to count audience size for segment filters"""

    filters: SegmentFilters


class AudienceCountResponse(BaseModel):
    """Response with audience count"""

    count: int
    filters: SegmentFilters
