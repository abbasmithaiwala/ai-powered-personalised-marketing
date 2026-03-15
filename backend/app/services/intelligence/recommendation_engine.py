"""
Recommendation engine for generating personalized menu item recommendations.

Uses vector similarity search combined with preference-based filtering
to suggest items customers are likely to enjoy.
"""

import structlog
from uuid import UUID
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from qdrant_client.models import Filter, FieldCondition, MatchAny

from app.db.vector_store import vector_store
from app.core.constants import (
    MENU_ITEM_EMBEDDINGS_COLLECTION,
    CUSTOMER_TASTE_PROFILES_COLLECTION,
)
from app.models.customer import Customer
from app.models.customer_preference import CustomerPreference
from app.models.menu_item import MenuItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.schemas.recommendation import RecommendationItem

logger = structlog.get_logger(__name__)


class RecommendationEngine:
    """
    Generate personalized recommendations using vector similarity search
    and preference-based filtering.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_recommendations(
        self,
        customer_id: UUID,
        limit: int = 5,
        exclude_recent_days: int = 30,
    ) -> tuple[List[RecommendationItem], bool]:
        """
        Generate personalized menu item recommendations for a customer.

        Args:
            customer_id: Customer UUID
            limit: Maximum number of recommendations to return
            exclude_recent_days: Exclude items ordered within this many days

        Returns:
            Tuple of (list of recommendations, fallback_used flag)

        Raises:
            ValueError: If customer not found
        """
        # Verify customer exists
        result = await self.db.execute(
            select(Customer)
            .options(selectinload(Customer.preference))
            .where(Customer.id == customer_id)
        )
        customer = result.scalar_one_or_none()

        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        # Try to get taste profile from Qdrant
        taste_profile_point = await vector_store.get_point(
            collection_name=CUSTOMER_TASTE_PROFILES_COLLECTION,
            point_id=str(customer_id),
        )

        if taste_profile_point and taste_profile_point.vector:
            # Use taste profile for personalized recommendations
            logger.info(
                "generating_personalized_recommendations",
                customer_id=str(customer_id),
            )
            recommendations = await self._generate_personalized_recommendations(
                customer_id=customer_id,
                taste_vector=taste_profile_point.vector,
                customer_preference=customer.preference,
                limit=limit,
                exclude_recent_days=exclude_recent_days,
            )
            fallback_used = False
        else:
            # Fallback to trending/popular items
            logger.info(
                "generating_fallback_recommendations",
                customer_id=str(customer_id),
                reason="no_taste_profile",
            )
            recommendations = await self._generate_fallback_recommendations(
                customer_id=customer_id,
                customer_preference=customer.preference,
                limit=limit,
                exclude_recent_days=exclude_recent_days,
            )
            fallback_used = True

        return recommendations, fallback_used

    async def _generate_personalized_recommendations(
        self,
        customer_id: UUID,
        taste_vector: List[float],
        customer_preference: Optional[CustomerPreference],
        limit: int,
        exclude_recent_days: int,
    ) -> List[RecommendationItem]:
        """
        Generate recommendations using vector similarity search.

        Strategy:
        1. Search menu item embeddings by cosine similarity
        2. Filter out recently ordered items
        3. Filter out items violating dietary restrictions
        4. Include at least one item from a new brand (if available)
        5. Build human-readable reasons from preferences
        """
        # Get recently ordered item IDs to exclude
        recently_ordered_item_ids = await self._get_recently_ordered_items(
            customer_id=customer_id,
            days=exclude_recent_days,
        )

        # Get customer's brand history
        customer_brand_ids = await self._get_customer_brand_ids(customer_id)

        # Build dietary filter from customer preferences
        dietary_restrictions = []
        if customer_preference and customer_preference.dietary_flags:
            # Extract dietary flags that are True
            for flag, value in customer_preference.dietary_flags.items():
                if value:
                    dietary_restrictions.append(flag)

        # Search for similar items in Qdrant
        # We'll request more than needed to allow for filtering
        search_limit = limit * 3  # Request 3x to account for filtering

        search_results = await vector_store.search(
            collection_name=MENU_ITEM_EMBEDDINGS_COLLECTION,
            query_vector=taste_vector,
            limit=search_limit,
        )

        # Process and filter results
        recommendations = []
        included_brand_ids = set()
        new_brand_item = None

        for result in search_results:
            if len(recommendations) >= limit:
                break

            payload = result.payload
            menu_item_id = UUID(payload.get("menu_item_id"))
            brand_id = UUID(payload.get("brand_id"))

            # Skip recently ordered items
            if menu_item_id in recently_ordered_item_ids:
                continue

            # Skip if violates dietary restrictions
            item_dietary_tags = payload.get("dietary_tags", [])
            if self._violates_dietary_restrictions(
                item_dietary_tags, dietary_restrictions
            ):
                continue

            # Fetch full menu item details
            menu_item = await self._get_menu_item_with_brand(menu_item_id)
            if not menu_item or not menu_item.is_available:
                continue

            # Build recommendation item
            score = result.score if hasattr(result, "score") else 0.0
            reason = self._build_recommendation_reason(
                menu_item=menu_item,
                customer_preference=customer_preference,
                is_new_brand=brand_id not in customer_brand_ids,
            )

            rec_item = RecommendationItem(
                menu_item_id=menu_item.id,
                name=menu_item.name,
                brand_name=menu_item.brand.name,
                brand_id=menu_item.brand_id,
                category=menu_item.category,
                cuisine_type=menu_item.cuisine_type,
                price=float(menu_item.price) if menu_item.price else None,
                score=min(1.0, max(0.0, float(score))),
                reason=reason,
            )

            # Track if this is from a new brand
            if brand_id not in customer_brand_ids and new_brand_item is None:
                new_brand_item = rec_item
                included_brand_ids.add(brand_id)
            else:
                recommendations.append(rec_item)
                included_brand_ids.add(brand_id)

        # Ensure at least one new brand item is included (if we found one)
        if new_brand_item and len(recommendations) < limit:
            recommendations.insert(0, new_brand_item)
        elif new_brand_item and len(recommendations) >= limit:
            # Replace last item with new brand item
            recommendations[-1] = new_brand_item

        return recommendations[:limit]

    async def _generate_fallback_recommendations(
        self,
        customer_id: UUID,
        customer_preference: Optional[CustomerPreference],
        limit: int,
        exclude_recent_days: int,
    ) -> List[RecommendationItem]:
        """
        Generate fallback recommendations using popular items.

        When no taste profile exists, recommend popular/trending items
        while still respecting dietary restrictions.
        """
        # Get recently ordered item IDs to exclude
        recently_ordered_item_ids = await self._get_recently_ordered_items(
            customer_id=customer_id,
            days=exclude_recent_days,
        )

        # Build dietary restrictions
        dietary_restrictions = []
        if customer_preference and customer_preference.dietary_flags:
            for flag, value in customer_preference.dietary_flags.items():
                if value:
                    dietary_restrictions.append(flag)

        # Query for popular items (most ordered)
        # Join with order_items to count orders
        from sqlalchemy import func

        stmt = (
            select(
                MenuItem,
                func.count(OrderItem.id).label("order_count"),
            )
            .join(OrderItem, OrderItem.menu_item_id == MenuItem.id)
            .where(MenuItem.is_available == True)
            .group_by(MenuItem.id)
            .order_by(func.count(OrderItem.id).desc())
            .limit(limit * 3)  # Request more to allow for filtering
            .options(selectinload(MenuItem.brand))
        )

        result = await self.db.execute(stmt)
        popular_items = result.all()

        recommendations = []
        for menu_item, order_count in popular_items:
            if len(recommendations) >= limit:
                break

            # Skip recently ordered items
            if menu_item.id in recently_ordered_item_ids:
                continue

            # Skip if violates dietary restrictions
            item_dietary_tags = menu_item.dietary_tags or []
            if self._violates_dietary_restrictions(
                item_dietary_tags, dietary_restrictions
            ):
                continue

            reason = f"Popular choice - ordered {order_count} times by our customers"

            rec_item = RecommendationItem(
                menu_item_id=menu_item.id,
                name=menu_item.name,
                brand_name=menu_item.brand.name,
                brand_id=menu_item.brand_id,
                category=menu_item.category,
                cuisine_type=menu_item.cuisine_type,
                price=float(menu_item.price) if menu_item.price else None,
                score=0.5,  # Neutral score for trending items
                reason=reason,
            )
            recommendations.append(rec_item)

        return recommendations

    async def _get_recently_ordered_items(
        self, customer_id: UUID, days: int
    ) -> set[UUID]:
        """Get set of menu item IDs ordered by customer in the last N days."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = (
            select(OrderItem.menu_item_id)
            .join(Order, Order.id == OrderItem.order_id)
            .where(
                Order.customer_id == customer_id,
                Order.order_date >= cutoff_date,
                OrderItem.menu_item_id.isnot(None),
            )
        )

        result = await self.db.execute(stmt)
        return {row[0] for row in result.all()}

    async def _get_customer_brand_ids(self, customer_id: UUID) -> set[UUID]:
        """Get set of brand IDs customer has ordered from."""
        stmt = select(Order.brand_id).where(Order.customer_id == customer_id).distinct()

        result = await self.db.execute(stmt)
        return {row[0] for row in result.all()}

    async def _get_menu_item_with_brand(self, menu_item_id: UUID) -> Optional[MenuItem]:
        """Fetch menu item with brand relationship loaded."""
        stmt = (
            select(MenuItem)
            .options(selectinload(MenuItem.brand))
            .where(MenuItem.id == menu_item_id)
        )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    def _violates_dietary_restrictions(
        self, item_dietary_tags: List[str], dietary_restrictions: List[str]
    ) -> bool:
        """
        Check if an item violates customer dietary restrictions.

        Logic: If customer is vegetarian, exclude non-vegetarian items.
        Item tags should include dietary information.
        """
        if not dietary_restrictions:
            return False

        # Normalize tags to lowercase
        item_tags_lower = [tag.lower() for tag in item_dietary_tags]

        for restriction in dietary_restrictions:
            restriction_lower = restriction.lower()

            # If customer is vegetarian, item must be tagged as vegetarian or vegan
            if restriction_lower == "vegetarian":
                if "vegetarian" not in item_tags_lower and "vegan" not in item_tags_lower:
                    return True
                continue  # Skip the generic check below

            # If customer is vegan, item must be tagged as vegan
            if restriction_lower == "vegan":
                if "vegan" not in item_tags_lower:
                    return True
                continue  # Skip the generic check below

            # For other restrictions (halal, gluten_free, etc.)
            # Item must have the matching tag
            if restriction_lower not in item_tags_lower:
                return True

        return False

    def _build_recommendation_reason(
        self,
        menu_item: MenuItem,
        customer_preference: Optional[CustomerPreference],
        is_new_brand: bool,
    ) -> str:
        """
        Build a human-readable reason for the recommendation.

        Uses customer preferences to explain why this item matches their taste.
        """
        reasons = []

        if not customer_preference:
            return "Recommended based on your order history"

        # Check cuisine match
        if (
            customer_preference.favorite_cuisines
            and menu_item.cuisine_type
        ):
            cuisine_lower = menu_item.cuisine_type.lower()
            for cuisine, score in customer_preference.favorite_cuisines.items():
                if cuisine.lower() in cuisine_lower or cuisine_lower in cuisine.lower():
                    if score >= 0.5:
                        reasons.append(f"your preference for {cuisine} cuisine")
                    break

        # Check category match
        if (
            customer_preference.favorite_categories
            and menu_item.category
        ):
            category_lower = menu_item.category.lower()
            for category, score in customer_preference.favorite_categories.items():
                if category.lower() in category_lower or category_lower in category.lower():
                    if score >= 0.5:
                        reasons.append(f"your love for {category}")
                    break

        # Check dietary match
        if customer_preference.dietary_flags and menu_item.dietary_tags:
            item_tags_lower = [tag.lower() for tag in menu_item.dietary_tags]
            for flag, value in customer_preference.dietary_flags.items():
                if value and flag.lower() in item_tags_lower:
                    reasons.append(f"matches your {flag} preference")
                    break

        # Note if from a new brand
        if is_new_brand:
            reasons.append("from a brand you haven't tried yet")

        if reasons:
            return "Matches " + " and ".join(reasons)
        else:
            return "Recommended based on your taste profile"
