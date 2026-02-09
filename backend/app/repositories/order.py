"""
Order repository for database operations.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.models.order_item import OrderItem


class OrderRepository:
    """Repository for order database operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize order repository.

        Args:
            session: Async database session
        """
        self.session = session

    async def get_by_id(self, order_id: UUID) -> Optional[Order]:
        """
        Get order by ID.

        Args:
            order_id: Order UUID

        Returns:
            Order if found, None otherwise
        """
        result = await self.session.execute(
            select(Order).where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_by_external_id(self, external_id: str) -> Optional[Order]:
        """
        Get order by external ID.

        Args:
            external_id: External order ID from POS/CSV

        Returns:
            Order if found, None otherwise
        """
        result = await self.session.execute(
            select(Order).where(Order.external_id == external_id)
        )
        return result.scalar_one_or_none()

    async def exists_by_external_id(self, external_id: str) -> bool:
        """
        Check if order exists by external ID.

        Args:
            external_id: External order ID

        Returns:
            True if order exists, False otherwise
        """
        order = await self.get_by_external_id(external_id)
        return order is not None

    async def create_with_items(
        self,
        customer_id: UUID,
        brand_id: UUID,
        order_date: datetime,
        items: list[dict],
        external_id: Optional[str] = None,
        total_amount: Optional[Decimal] = None,
        channel: Optional[str] = None,
    ) -> Order:
        """
        Create a new order with order items in a single transaction.

        Args:
            customer_id: Customer UUID
            brand_id: Brand UUID
            order_date: Order date
            items: List of item dicts with keys: item_name, quantity, unit_price, subtotal, menu_item_id (optional)
            external_id: External order ID from POS
            total_amount: Order total amount
            channel: Order channel

        Returns:
            Created order with items
        """
        # Create order
        order = Order(
            customer_id=customer_id,
            brand_id=brand_id,
            order_date=order_date,
            external_id=external_id,
            total_amount=total_amount,
            channel=channel,
        )
        self.session.add(order)
        await self.session.flush()

        # Create order items
        for item_data in items:
            order_item = OrderItem(
                order_id=order.id,
                item_name=item_data["item_name"],
                quantity=item_data["quantity"],
                unit_price=item_data.get("unit_price"),
                subtotal=item_data.get("subtotal"),
                menu_item_id=item_data.get("menu_item_id"),
            )
            self.session.add(order_item)

        await self.session.flush()
        await self.session.refresh(order)

        return order
