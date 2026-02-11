"""Dashboard metrics API endpoints"""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.db.session import get_db
from app.models.customer import Customer
from app.models.order import Order
from app.models.campaign import Campaign
from app.models.campaign_recipient import CampaignRecipient

router = APIRouter()


class DashboardMetricsResponse(BaseModel):
    """Dashboard metrics response"""
    total_customers: int
    total_orders_30d: int
    active_campaigns: int
    messages_generated: int


@router.get("/metrics", response_model=DashboardMetricsResponse)
async def get_dashboard_metrics(
    db: AsyncSession = Depends(get_db),
):
    """
    Get dashboard metrics.

    Returns:
    - Total customers: Count of all customers in the database
    - Total orders (30d): Count of orders in the last 30 days
    - Active campaigns: Count of campaigns not in 'completed' or 'failed' status
    - Messages generated: Total count of successfully generated campaign messages
    """
    # Total customers
    customer_count_stmt = select(func.count(Customer.id))
    customer_result = await db.execute(customer_count_stmt)
    total_customers = customer_result.scalar_one()

    # Orders in last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    orders_30d_stmt = select(func.count(Order.id)).where(
        Order.order_date >= thirty_days_ago
    )
    orders_result = await db.execute(orders_30d_stmt)
    total_orders_30d = orders_result.scalar_one()

    # Active campaigns (not completed or failed)
    active_campaigns_stmt = select(func.count(Campaign.id)).where(
        Campaign.status.in_(['draft', 'previewing', 'ready', 'executing'])
    )
    campaigns_result = await db.execute(active_campaigns_stmt)
    active_campaigns = campaigns_result.scalar_one()

    # Total messages generated
    messages_stmt = select(func.count(CampaignRecipient.id)).where(
        CampaignRecipient.status == 'generated'
    )
    messages_result = await db.execute(messages_stmt)
    messages_generated = messages_result.scalar_one()

    return DashboardMetricsResponse(
        total_customers=total_customers,
        total_orders_30d=total_orders_30d,
        active_campaigns=active_campaigns,
        messages_generated=messages_generated,
    )
