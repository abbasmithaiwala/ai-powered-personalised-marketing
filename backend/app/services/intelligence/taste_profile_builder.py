"""
Service for building and managing customer taste profile vectors.

Aggregates embeddings from a customer's order history to create a personalized
taste profile vector for semantic recommendations.
"""

import structlog
from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime, timezone
import math

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue

from app.models.customer import Customer
from app.models.order import Order
from app.models.order_item import OrderItem
from app.db.vector_store import vector_store
from app.core.constants import (
    MENU_ITEM_EMBEDDINGS_COLLECTION,
    CUSTOMER_TASTE_PROFILES_COLLECTION,
    VECTOR_DIMENSION,
)

logger = structlog.get_logger(__name__)


class TasteProfileBuilder:
    """
    Service for building customer taste profile vectors.

    Creates personalized taste profiles by aggregating embeddings from
    a customer's order history with recency weighting.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize taste profile builder.

        Args:
            session: Async database session
        """
        self.session = session

    @staticmethod
    def compute_recency_weight(order_date: datetime) -> float:
        """
        Compute exponential decay weight based on days since order.

        Uses formula: exp(-days_since_order / 90.0)

        Args:
            order_date: Timestamp of the order

        Returns:
            Weight between 0 and 1 (1 = today, approaches 0 as time increases)
        """
        now = datetime.now(timezone.utc)

        # Make order_date timezone-aware if it isn't
        if order_date.tzinfo is None:
            order_date = order_date.replace(tzinfo=timezone.utc)

        days_since = (now - order_date).total_seconds() / 86400.0  # seconds to days

        # Exponential decay with 90-day half-life
        # Recent orders (0-30 days): ~0.7-1.0
        # Medium age (30-90 days): ~0.4-0.7
        # Older (90-180 days): ~0.1-0.4
        weight = math.exp(-days_since / 90.0)

        return weight

    async def build_taste_profile(self, customer_id: UUID) -> Optional[Dict]:
        """
        Build or update a customer's taste profile vector.

        Algorithm:
        1. Fetch all order items with timestamps
        2. For each item, retrieve its embedding from Qdrant
        3. Compute recency weight based on order date
        4. Calculate weighted average of all item vectors
        5. L2 normalize the result
        6. Upsert into Qdrant customer_taste_profiles

        Args:
            customer_id: UUID of the customer

        Returns:
            Dictionary with status and metadata, or None if failed
        """
        if not vector_store.is_connected:
            logger.warning(
                "vector_store_not_connected",
                operation="build_taste_profile",
                customer_id=str(customer_id),
            )
            return None

        # Fetch customer with order history
        result = await self.session.execute(
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
            logger.warning(
                "customer_not_found",
                customer_id=str(customer_id),
            )
            return None

        if not customer.orders:
            logger.info(
                "customer_no_orders",
                customer_id=str(customer_id),
                message="Customer has no order history, skipping taste profile",
            )
            return {
                "status": "insufficient_data",
                "customer_id": str(customer_id),
                "reason": "no_orders",
            }

        # Collect item embeddings with weights
        weighted_embeddings = []
        total_weight = 0.0
        items_processed = 0
        items_skipped = 0

        for order in customer.orders:
            for order_item in order.order_items:
                # Skip items without linked menu items
                if not order_item.menu_item or not order_item.menu_item.embedding_id:
                    items_skipped += 1
                    continue

                # Fetch embedding from Qdrant
                item_embedding = await self._get_item_embedding(
                    order_item.menu_item.id
                )

                if not item_embedding:
                    items_skipped += 1
                    continue

                # Compute recency weight
                weight = self.compute_recency_weight(order.order_date)

                # Apply quantity multiplier (if customer ordered 3x, weight 3x more)
                quantity = order_item.quantity or 1
                effective_weight = weight * quantity

                weighted_embeddings.append((item_embedding, effective_weight))
                total_weight += effective_weight
                items_processed += 1

        if not weighted_embeddings:
            logger.info(
                "customer_no_embedded_items",
                customer_id=str(customer_id),
                items_skipped=items_skipped,
            )
            return {
                "status": "insufficient_data",
                "customer_id": str(customer_id),
                "reason": "no_embedded_items",
                "items_skipped": items_skipped,
            }

        # Compute weighted average
        profile_vector = [0.0] * VECTOR_DIMENSION

        for embedding, weight in weighted_embeddings:
            for i in range(len(embedding)):
                profile_vector[i] += embedding[i] * weight

        # Normalize by total weight (weighted average)
        if total_weight > 0:
            profile_vector = [val / total_weight for val in profile_vector]

        # L2 normalize the profile vector
        profile_vector = self._l2_normalize(profile_vector)

        # Upsert to Qdrant
        success = await self._upsert_taste_profile(
            customer_id=customer_id,
            profile_vector=profile_vector,
        )

        if success:
            logger.info(
                "taste_profile_built",
                customer_id=str(customer_id),
                items_processed=items_processed,
                items_skipped=items_skipped,
                total_weight=round(total_weight, 2),
            )
            return {
                "status": "success",
                "customer_id": str(customer_id),
                "items_processed": items_processed,
                "items_skipped": items_skipped,
                "total_weight": round(total_weight, 2),
            }
        else:
            logger.error(
                "taste_profile_upsert_failed",
                customer_id=str(customer_id),
            )
            return {
                "status": "failed",
                "customer_id": str(customer_id),
                "reason": "upsert_failed",
            }

    async def _get_item_embedding(self, menu_item_id: UUID) -> Optional[List[float]]:
        """
        Retrieve a menu item's embedding vector from Qdrant.

        Args:
            menu_item_id: Menu item UUID

        Returns:
            Embedding vector as list of floats, or None if not found
        """
        try:
            point = await vector_store.get_point(
                collection_name=MENU_ITEM_EMBEDDINGS_COLLECTION,
                point_id=str(menu_item_id),
            )

            if point and hasattr(point, 'vector'):
                return point.vector

            logger.debug(
                "item_embedding_not_found",
                menu_item_id=str(menu_item_id),
            )
            return None

        except Exception as e:
            logger.error(
                "item_embedding_retrieval_failed",
                menu_item_id=str(menu_item_id),
                error=str(e),
            )
            return None

    @staticmethod
    def _l2_normalize(vector: List[float]) -> List[float]:
        """
        L2 normalize a vector (make its magnitude = 1).

        Args:
            vector: Input vector

        Returns:
            L2 normalized vector
        """
        magnitude = math.sqrt(sum(x * x for x in vector))

        if magnitude == 0:
            # Avoid division by zero - return zero vector
            return vector

        return [x / magnitude for x in vector]

    async def _upsert_taste_profile(
        self,
        customer_id: UUID,
        profile_vector: List[float],
    ) -> bool:
        """
        Upsert a customer's taste profile to Qdrant.

        Args:
            customer_id: Customer UUID
            profile_vector: Taste profile embedding vector

        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {
                "customer_id": str(customer_id),
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }

            point = PointStruct(
                id=str(customer_id),  # Use customer UUID as point ID
                vector=profile_vector,
                payload=payload,
            )

            success = await vector_store.upsert_points(
                collection_name=CUSTOMER_TASTE_PROFILES_COLLECTION,
                points=[point],
            )

            return success

        except Exception as e:
            logger.error(
                "taste_profile_upsert_error",
                customer_id=str(customer_id),
                error=str(e),
            )
            return False

    async def delete_taste_profile(self, customer_id: UUID) -> bool:
        """
        Delete a customer's taste profile from Qdrant.

        Args:
            customer_id: Customer UUID

        Returns:
            True if successful, False otherwise
        """
        if not vector_store.is_connected:
            logger.warning(
                "vector_store_not_connected",
                operation="delete_taste_profile",
                customer_id=str(customer_id),
            )
            return False

        from qdrant_client.models import PointIdsList

        success = await vector_store.delete_points(
            collection_name=CUSTOMER_TASTE_PROFILES_COLLECTION,
            points_selector=PointIdsList(points=[str(customer_id)]),
        )

        if success:
            logger.info(
                "taste_profile_deleted",
                customer_id=str(customer_id),
            )
        else:
            logger.error(
                "taste_profile_delete_failed",
                customer_id=str(customer_id),
            )

        return success

    async def get_taste_profile(self, customer_id: UUID) -> Optional[Dict]:
        """
        Retrieve a customer's taste profile from Qdrant.

        Args:
            customer_id: Customer UUID

        Returns:
            Dictionary with profile data, or None if not found
        """
        if not vector_store.is_connected:
            logger.warning(
                "vector_store_not_connected",
                operation="get_taste_profile",
                customer_id=str(customer_id),
            )
            return None

        try:
            point = await vector_store.get_point(
                collection_name=CUSTOMER_TASTE_PROFILES_COLLECTION,
                point_id=str(customer_id),
            )

            if point:
                return {
                    "customer_id": str(customer_id),
                    "vector": point.vector,
                    "last_updated": point.payload.get("last_updated"),
                }

            return None

        except Exception as e:
            logger.error(
                "taste_profile_retrieval_failed",
                customer_id=str(customer_id),
                error=str(e),
            )
            return None
