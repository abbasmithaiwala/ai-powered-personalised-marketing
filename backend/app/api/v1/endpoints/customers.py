"""Customer API endpoints"""

from uuid import UUID
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.services.intelligence import PreferenceEngine
from app.services.segmentation_service import SegmentationService
from app.schemas.customer_preference import CustomerPreferenceResponse
from app.schemas.campaign import SegmentFilters

router = APIRouter()


# ============================================================================
# Response Schemas
# ============================================================================


class CustomerResponse(BaseModel):
    """Customer response schema"""

    id: UUID
    external_id: str | None
    email: str | None
    phone: str | None
    first_name: str | None
    last_name: str | None
    city: str | None
    total_orders: int
    total_spend: float
    first_order_at: datetime | None
    last_order_at: datetime | None

    model_config = {"from_attributes": True}


class CustomerSearchRequest(BaseModel):
    """Request schema for customer search"""

    filters: Optional[SegmentFilters] = Field(
        None,
        description="Filter criteria",
    )
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(25, ge=1, le=100, description="Number of results per page")


class CustomerSearchResponse(BaseModel):
    """Response schema for customer search"""

    items: List[CustomerResponse]
    total: int
    page: int
    page_size: int
    pages: int


class SegmentCountRequest(BaseModel):
    """Request schema for segment count"""

    filters: Optional[SegmentFilters] = Field(
        None,
        description="Filter criteria",
    )


class SegmentCountResponse(BaseModel):
    """Response schema for segment count"""

    count: int


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/search", response_model=CustomerSearchResponse)
async def search_customers(
    request: CustomerSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Search customers matching segment filters with pagination.

    All filters combine with AND logic. Empty filters return all customers.

    Supported filters:
    - last_order_after/before: Date range for last order
    - total_spend_min/max: Spend amount range
    - total_orders_min: Minimum order count
    - favorite_cuisine: Filter by preferred cuisine from profile
    - dietary_flag: Filter by dietary restriction (vegetarian, vegan, halal, gluten_free)
    - city: Filter by customer city (case-insensitive partial match)
    - order_frequency: Filter by order frequency (daily, weekly, monthly, occasional)
    - brand_id: Filter customers who ordered from specific brand
    """
    service = SegmentationService(db)

    # Calculate offset from page
    offset = (request.page - 1) * request.page_size

    # Use empty filters if none provided
    filters = request.filters or SegmentFilters(
        last_order_after=None,
        last_order_before=None,
        total_spend_min=None,
        total_spend_max=None,
        total_orders_min=None,
        favorite_cuisine=None,
        dietary_flag=None,
        city=None,
        order_frequency=None,
        brand_id=None,
    )

    # Search customers
    customers, total = await service.find_customers(
        filters=filters,
        limit=request.page_size,
        offset=offset,
    )

    # Calculate total pages
    pages = (total + request.page_size - 1) // request.page_size

    return CustomerSearchResponse(
        items=[CustomerResponse.model_validate(c) for c in customers],
        total=total,
        page=request.page,
        page_size=request.page_size,
        pages=pages,
    )


@router.post("/segment-count", response_model=SegmentCountResponse)
async def get_segment_count(
    request: SegmentCountRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Fast count of customers matching segment filters.

    Used by campaign creation to show estimated audience size
    as filters are adjusted.

    Target response time: <200ms for MVP scale.
    """
    service = SegmentationService(db)

    # Use empty filters if none provided
    filters = request.filters or SegmentFilters(
        last_order_after=None,
        last_order_before=None,
        total_spend_min=None,
        total_spend_max=None,
        total_orders_min=None,
        favorite_cuisine=None,
        dietary_flag=None,
        city=None,
        order_frequency=None,
        brand_id=None,
    )

    count = await service.count_segment(filters)

    return SegmentCountResponse(count=count)


@router.post(
    "/{customer_id}/recompute-preferences", response_model=CustomerPreferenceResponse
)
async def recompute_customer_preferences(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Recompute preference signals for a specific customer based on their order history.

    This endpoint analyzes the customer's full order history and updates:
    - Favorite cuisines (with recency weighting)
    - Favorite categories
    - Dietary flags
    - Price sensitivity
    - Order frequency
    - Brand affinity
    - Preferred order times
    """
    try:
        engine = PreferenceEngine(db)
        preference = await engine.compute_preferences(customer_id)

        return CustomerPreferenceResponse.model_validate(preference)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to compute preferences: {str(e)}"
        )
