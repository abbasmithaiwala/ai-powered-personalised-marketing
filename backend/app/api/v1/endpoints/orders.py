"""Order API endpoints"""

from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import List

from app.db.session import get_db
from app.models import Customer, Order

router = APIRouter()


class OrderResponse(BaseModel):
    """Order response schema"""

    id: UUID
    external_id: str | None
    customer_id: UUID
    brand_id: UUID
    order_date: datetime
    total_amount: float | None
    channel: str | None

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    """Paginated order list response"""

    items: List[OrderResponse]
    total: int
    page: int
    page_size: int
    pages: int


@router.get("/{customer_id}/orders", response_model=OrderListResponse)
async def get_customer_orders(
    customer_id: UUID,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of results per page"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get order history for a specific customer.

    Returns paginated list of orders sorted by order_date descending.
    """
    # Verify customer exists
    customer_result = await db.execute(
        select(Customer).where(Customer.id == customer_id)
    )
    customer = customer_result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Get total count
    count_result = await db.execute(
        select(func.count(Order.id)).where(Order.customer_id == customer_id)
    )
    total = count_result.scalar_one()

    # Get orders with pagination
    offset = (page - 1) * page_size
    orders_result = await db.execute(
        select(Order)
        .where(Order.customer_id == customer_id)
        .order_by(Order.order_date.desc())
        .limit(page_size)
        .offset(offset)
    )
    orders = list(orders_result.scalars().all())

    # Calculate total pages
    pages = (total + page_size - 1) // page_size

    return OrderListResponse(
        items=[OrderResponse.model_validate(o) for o in orders],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )
