"""
Customer repository for database operations.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer


class CustomerRepository:
    """Repository for customer database operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize customer repository.

        Args:
            session: Async database session
        """
        self.session = session

    async def get_by_id(self, customer_id: UUID) -> Optional[Customer]:
        """
        Get customer by ID.

        Args:
            customer_id: Customer UUID

        Returns:
            Customer if found, None otherwise
        """
        result = await self.session.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        return result.scalar_one_or_none()

    async def get_by_external_id(self, external_id: str) -> Optional[Customer]:
        """
        Get customer by external ID.

        Args:
            external_id: External customer ID from POS/CSV

        Returns:
            Customer if found, None otherwise
        """
        result = await self.session.execute(
            select(Customer).where(Customer.external_id == external_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[Customer]:
        """
        Get customer by email (case-insensitive).

        Args:
            email: Customer email

        Returns:
            Customer if found, None otherwise
        """
        result = await self.session.execute(
            select(Customer).where(Customer.email.ilike(email))
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        email: str,
        external_id: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        city: Optional[str] = None,
        **kwargs
    ) -> Customer:
        """
        Create a new customer.

        Args:
            email: Customer email
            external_id: External ID from POS
            first_name: Customer first name
            last_name: Customer last name
            phone: Customer phone
            city: Customer city
            **kwargs: Additional customer attributes

        Returns:
            Created customer
        """
        customer = Customer(
            email=email,
            external_id=external_id,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            city=city,
            **kwargs
        )
        self.session.add(customer)
        await self.session.flush()
        await self.session.refresh(customer)
        return customer

    async def get_or_create(
        self,
        email: str,
        external_id: Optional[str] = None,
        **kwargs
    ) -> tuple[Customer, bool]:
        """
        Get existing customer or create new one.

        Lookup strategy:
        1. Try external_id if provided
        2. Fall back to email

        Args:
            email: Customer email
            external_id: External ID from POS
            **kwargs: Additional customer attributes

        Returns:
            Tuple of (customer, created) where created is True if customer was created
        """
        customer = None

        # Try external_id first if provided
        if external_id:
            customer = await self.get_by_external_id(external_id)

        # Fall back to email
        if not customer:
            customer = await self.get_by_email(email)

        if customer:
            return customer, False

        # Create new customer
        customer = await self.create(
            email=email,
            external_id=external_id,
            **kwargs
        )
        return customer, True

    async def update_order_stats(
        self,
        customer_id: UUID,
        order_total: Decimal,
        order_date: datetime,
    ) -> None:
        """
        Update customer aggregate statistics after an order.

        Args:
            customer_id: Customer UUID
            order_total: Order total amount
            order_date: Order date
        """
        customer = await self.get_by_id(customer_id)
        if not customer:
            return

        # Increment counts
        customer.total_orders += 1
        customer.total_spend = float(customer.total_spend) + float(order_total)

        # Update first/last order dates
        # Make order_date timezone-aware if customer dates are timezone-aware
        if customer.first_order_at is not None and customer.first_order_at.tzinfo is not None:
            if order_date.tzinfo is None:
                from datetime import timezone
                order_date = order_date.replace(tzinfo=timezone.utc)

        if customer.first_order_at is None or order_date < customer.first_order_at:
            customer.first_order_at = order_date

        if customer.last_order_at is None or order_date > customer.last_order_at:
            customer.last_order_at = order_date

        await self.session.flush()
