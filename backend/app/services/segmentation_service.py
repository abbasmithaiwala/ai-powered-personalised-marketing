"""Customer segmentation service for filtering and searching customers"""

import logging
from typing import List, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models import Customer, CustomerPreference, Order
from app.schemas.campaign import SegmentFilters

logger = logging.getLogger(__name__)


class SegmentationService:
    """
    Service for customer segmentation and filtering.

    Used by campaigns to find customers matching specific criteria.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def count_segment(self, filters: SegmentFilters) -> int:
        """
        Count customers matching segment filters.

        Args:
            filters: Segment filter criteria

        Returns:
            Number of customers matching filters
        """
        query = self._build_query(filters, count_only=True)
        result = await self.db.execute(query)
        count = result.scalar_one()
        return count

    async def find_customers(
        self, filters: SegmentFilters, limit: int = 100, offset: int = 0
    ) -> Tuple[List[Customer], int]:
        """
        Find customers matching segment filters with pagination.

        Args:
            filters: Segment filter criteria
            limit: Maximum number of customers to return
            offset: Number of customers to skip

        Returns:
            Tuple of (list of customers, total count)
        """
        # Get total count
        total = await self.count_segment(filters)

        # Get customers
        query = self._build_query(filters, count_only=False)
        query = query.limit(limit).offset(offset)
        query = query.options(selectinload(Customer.preference))

        result = await self.db.execute(query)
        customers = list(result.scalars().all())

        logger.info(
            f"Found {len(customers)} customers (total: {total}) "
            f"matching segment filters"
        )

        return customers, total

    def _build_query(self, filters: SegmentFilters, count_only: bool = False):
        """
        Build SQLAlchemy query from segment filters.

        Args:
            filters: Segment filter criteria
            count_only: If True, return count query; if False, return select query

        Returns:
            SQLAlchemy query
        """
        if count_only:
            query = select(func.count(Customer.id))
        else:
            query = select(Customer)

        conditions = []

        # Search filter (name, email, external_id)
        if filters.search:
            search_term = f"%{filters.search}%"
            search_conditions = [
                Customer.first_name.ilike(search_term),
                Customer.last_name.ilike(search_term),
                Customer.email.ilike(search_term),
                Customer.external_id.ilike(search_term),
            ]
            conditions.append(or_(*search_conditions))

        # Date filters (require subquery on orders)
        if filters.last_order_after or filters.last_order_before:
            if filters.last_order_after:
                conditions.append(Customer.last_order_at >= filters.last_order_after)
            if filters.last_order_before:
                conditions.append(Customer.last_order_at <= filters.last_order_before)

        # Spend filters
        if filters.total_spend_min is not None:
            conditions.append(Customer.total_spend >= filters.total_spend_min)
        if filters.total_spend_max is not None:
            conditions.append(Customer.total_spend <= filters.total_spend_max)

        # Order count filters
        if filters.total_orders_min is not None:
            conditions.append(Customer.total_orders >= filters.total_orders_min)

        # City filter - support multiple cities separated by commas
        if filters.city:
            cities = [city.strip() for city in filters.city.split(",") if city.strip()]
            if len(cities) == 1:
                conditions.append(Customer.city.ilike(f"%{cities[0]}%"))
            elif len(cities) > 1:
                # Create OR conditions for each city
                city_conditions = [Customer.city.ilike(f"%{city}%") for city in cities]
                conditions.append(or_(*city_conditions))

        # Preference-based filters (require join with customer_preferences)
        preference_conditions = []

        if filters.favorite_cuisine:
            # Check if cuisine exists in favorite_cuisines JSONB (case-insensitive)
            # Convert to lowercase for matching since keys are stored in lowercase
            cuisine_key = filters.favorite_cuisine.lower()
            preference_conditions.append(
                CustomerPreference.favorite_cuisines.has_key(cuisine_key)
            )

        if filters.dietary_flag:
            # Check if dietary flag is true in dietary_flags JSONB
            preference_conditions.append(
                CustomerPreference.dietary_flags[filters.dietary_flag].astext == "true"
            )

        if filters.order_frequency:
            preference_conditions.append(
                CustomerPreference.order_frequency == filters.order_frequency
            )

        # If we have preference conditions, join with customer_preferences
        if preference_conditions:
            query = query.join(
                CustomerPreference, Customer.id == CustomerPreference.customer_id
            )
            conditions.extend(preference_conditions)

        # Brand filter (requires subquery on orders)
        if filters.brand_id:
            # Subquery to find customers who ordered from this brand
            brand_customer_subquery = (
                select(Order.customer_id)
                .where(Order.brand_id == filters.brand_id)
                .distinct()
                .subquery()
            )
            conditions.append(Customer.id.in_(select(brand_customer_subquery)))

        # Apply all conditions
        if conditions:
            query = query.where(and_(*conditions))

        # Order by most recent customers first (for non-count queries)
        if not count_only:
            query = query.order_by(Customer.last_order_at.desc().nulls_last())

        return query
