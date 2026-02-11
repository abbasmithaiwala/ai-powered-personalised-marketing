"""Main preference computation engine"""

import structlog
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = structlog.get_logger(__name__)

from app.models.customer import Customer
from app.models.customer_preference import CustomerPreference
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.menu_item import MenuItem
from app.models.brand import Brand

from .cuisine_analyzer import CuisineAnalyzer
from .dietary_analyzer import DietaryAnalyzer
from .price_analyzer import PriceAnalyzer
from .timing_analyzer import TimingAnalyzer
from .taste_profile_builder import TasteProfileBuilder


class PreferenceEngine:
    """
    Main orchestrator for computing customer preferences from order history.

    This engine analyzes a customer's full order history and computes:
    - Favorite cuisines (with recency weighting)
    - Favorite categories (mains, desserts, etc.)
    - Dietary flags (vegetarian, vegan, etc.)
    - Price sensitivity (low, medium, high)
    - Order frequency (daily, weekly, monthly, occasional)
    - Preferred order times (breakfast, lunch, dinner, late_night)
    - Brand affinity (preference scores per brand)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def compute_preferences(self, customer_id: UUID) -> CustomerPreference:
        """
        Compute or update preferences for a given customer.

        Args:
            customer_id: UUID of the customer

        Returns:
            CustomerPreference object with computed signals

        Raises:
            ValueError: If customer not found
        """
        # Fetch customer with all related data
        result = await self.db.execute(
            select(Customer)
            .options(
                selectinload(Customer.orders)
                .selectinload(Order.order_items)
                .selectinload(OrderItem.menu_item)
            )
            .where(Customer.id == customer_id)
        )
        customer = result.scalar_one_or_none()

        if not customer:
            raise ValueError(f"Customer not found: {customer_id}")

        # If customer has no orders, create minimal preference record
        if not customer.orders:
            return await self._create_or_update_preference(
                customer_id=customer_id,
                favorite_cuisines={},
                favorite_categories={},
                dietary_flags={},
                price_sensitivity="medium",
                order_frequency="occasional",
                brand_affinity=[],
                preferred_order_times={},
            )

        # Prepare data structures for analyzers
        cuisine_data = []  # (order_date, cuisine_type, quantity)
        category_data = []  # (order_date, category, quantity)
        dietary_data = []  # (order_date, dietary_tags)
        order_totals = []  # List of order total amounts
        order_dates = []  # List of order timestamps
        brand_orders = {}  # brand_id -> list of (order_date, total_amount)

        for order in customer.orders:
            order_dates.append(order.order_date)

            if order.total_amount:
                order_totals.append(float(order.total_amount))

            # Track brand orders for affinity
            if order.brand_id not in brand_orders:
                brand_orders[order.brand_id] = []
            brand_orders[order.brand_id].append((order.order_date, order.total_amount or 0))

            for order_item in order.order_items:
                quantity = order_item.quantity or 1

                if order_item.menu_item:
                    # Extract cuisine type
                    if order_item.menu_item.cuisine_type:
                        cuisine_data.append(
                            (order.order_date, order_item.menu_item.cuisine_type, quantity)
                        )

                    # Extract category
                    if order_item.menu_item.category:
                        category_data.append(
                            (order.order_date, order_item.menu_item.category, quantity)
                        )

                    # Extract dietary tags
                    if order_item.menu_item.dietary_tags:
                        dietary_data.append(
                            (order.order_date, order_item.menu_item.dietary_tags)
                        )

        # Compute all preference signals
        favorite_cuisines = CuisineAnalyzer.analyze(cuisine_data)
        favorite_categories = self._analyze_categories(category_data)
        dietary_flags = DietaryAnalyzer.analyze(dietary_data)
        price_sensitivity = PriceAnalyzer.analyze(order_totals)
        order_frequency = TimingAnalyzer.compute_order_frequency(order_dates)
        preferred_order_times = TimingAnalyzer.compute_preferred_order_times(order_dates)
        brand_affinity = await self._analyze_brand_affinity(brand_orders)

        # Create or update preference record
        preference = await self._create_or_update_preference(
            customer_id=customer_id,
            favorite_cuisines=favorite_cuisines,
            favorite_categories=favorite_categories,
            dietary_flags=dietary_flags,
            price_sensitivity=price_sensitivity,
            order_frequency=order_frequency,
            brand_affinity=brand_affinity,
            preferred_order_times=preferred_order_times,
        )

        # Trigger taste profile computation
        # This is critical for personalized recommendations to work
        try:
            taste_builder = TasteProfileBuilder(self.db)
            taste_result = await taste_builder.build_taste_profile(customer_id)

            if taste_result is None:
                logger.warning(
                    "taste_profile_not_created",
                    customer_id=str(customer_id),
                    reason="vector_store_not_connected_or_customer_not_found",
                )
            elif taste_result.get("status") != "success":
                logger.warning(
                    "taste_profile_build_issue",
                    customer_id=str(customer_id),
                    status=taste_result.get("status"),
                    reason=taste_result.get("reason"),
                )
            else:
                logger.info(
                    "taste_profile_built",
                    customer_id=str(customer_id),
                    items_processed=taste_result.get("items_processed"),
                )
        except Exception as e:
            logger.error(
                "taste_profile_build_failed",
                customer_id=str(customer_id),
                error=str(e),
            )

        return preference

    def _analyze_categories(self, category_data: list) -> dict:
        """
        Analyze category preferences with recency weighting.

        Similar to cuisine analysis but for food categories.
        """
        if not category_data:
            return {}

        from collections import defaultdict

        category_scores = defaultdict(float)

        for order_date, category, quantity in category_data:
            if not category:
                continue

            # Normalize category name
            cat = category.lower().strip()

            # Apply time decay weight
            time_weight = CuisineAnalyzer.compute_time_weight(order_date)

            # Weight by quantity
            category_scores[cat] += time_weight * quantity

        if not category_scores:
            return {}

        # Normalize to 0-1 range
        max_score = max(category_scores.values())
        normalized = {cat: score / max_score for cat, score in category_scores.items()}

        # Keep top 5 categories
        top_categories = sorted(normalized.items(), key=lambda x: x[1], reverse=True)[
            :5
        ]

        return dict(top_categories)

    async def _analyze_brand_affinity(self, brand_orders: dict) -> list:
        """
        Compute brand affinity scores with recency weighting.

        Args:
            brand_orders: Dict of brand_id -> list of (order_date, amount)

        Returns:
            List of {brand_id, brand_name, score} sorted by score desc
        """
        if not brand_orders:
            return []

        brand_scores = {}

        for brand_id, orders in brand_orders.items():
            total_weighted_score = 0.0

            for order_date, amount in orders:
                # Apply time decay
                time_weight = CuisineAnalyzer.compute_time_weight(order_date)
                total_weighted_score += time_weight

            brand_scores[brand_id] = total_weighted_score

        # Normalize to 0-1 range
        max_score = max(brand_scores.values()) if brand_scores else 1.0
        normalized_scores = {
            brand_id: score / max_score for brand_id, score in brand_scores.items()
        }

        # Fetch brand names
        brand_ids = list(normalized_scores.keys())
        result = await self.db.execute(select(Brand).where(Brand.id.in_(brand_ids)))
        brands = result.scalars().all()

        brand_name_map = {brand.id: brand.name for brand in brands}

        # Build affinity list
        affinity_list = [
            {
                "brand_id": str(brand_id),
                "brand_name": brand_name_map.get(brand_id, "Unknown"),
                "score": round(score, 3),
            }
            for brand_id, score in normalized_scores.items()
        ]

        # Sort by score descending
        affinity_list.sort(key=lambda x: x["score"], reverse=True)

        return affinity_list

    async def _create_or_update_preference(
        self,
        customer_id: UUID,
        favorite_cuisines: dict,
        favorite_categories: dict,
        dietary_flags: dict,
        price_sensitivity: str,
        order_frequency: str,
        brand_affinity: list,
        preferred_order_times: dict,
    ) -> CustomerPreference:
        """Create or update customer preference record"""

        # Check if preference already exists
        result = await self.db.execute(
            select(CustomerPreference).where(
                CustomerPreference.customer_id == customer_id
            )
        )
        preference = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)

        if preference:
            # Update existing preference
            preference.favorite_cuisines = favorite_cuisines
            preference.favorite_categories = favorite_categories
            preference.dietary_flags = dietary_flags
            preference.price_sensitivity = price_sensitivity
            preference.order_frequency = order_frequency
            preference.brand_affinity = brand_affinity
            preference.preferred_order_times = preferred_order_times
            preference.last_computed_at = now
            preference.version += 1
        else:
            # Create new preference
            preference = CustomerPreference(
                customer_id=customer_id,
                favorite_cuisines=favorite_cuisines,
                favorite_categories=favorite_categories,
                dietary_flags=dietary_flags,
                price_sensitivity=price_sensitivity,
                order_frequency=order_frequency,
                brand_affinity=brand_affinity,
                preferred_order_times=preferred_order_times,
                last_computed_at=now,
                version=1,
            )
            self.db.add(preference)

        await self.db.commit()
        await self.db.refresh(preference)

        return preference
