"""
Service for building and managing menu item embeddings in Qdrant.
"""

import structlog
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from qdrant_client.models import PointStruct

from app.models.menu_item import MenuItem
from app.services.embedding_service import embedding_service
from app.db.vector_store import vector_store
from app.core.constants import MENU_ITEM_EMBEDDINGS_COLLECTION

logger = structlog.get_logger(__name__)


class EmbeddingBuilder:
    """
    Service for generating and managing menu item embeddings.

    Builds semantic embeddings from menu item data and stores them in Qdrant
    for similarity-based search and recommendations.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize embedding builder.

        Args:
            session: Async database session
        """
        self.session = session

    def build_item_text(self, item: MenuItem) -> str:
        """
        Construct embedding text from menu item fields.

        Combines name, cuisine, category, description, and tags into a single
        text representation optimized for semantic search.

        Args:
            item: Menu item model instance

        Returns:
            Concatenated text string for embedding generation
        """
        parts = []

        # Core identity
        if item.name:
            parts.append(item.name)

        # Cuisine and category context
        cuisine_category = []
        if item.cuisine_type:
            cuisine_category.append(item.cuisine_type)
        if item.category:
            cuisine_category.append(item.category)
        if cuisine_category:
            parts.append(" ".join(cuisine_category))

        # Description
        if item.description:
            parts.append(item.description)

        # Flavor profile
        if item.flavor_tags and len(item.flavor_tags) > 0:
            parts.append(f"flavors: {', '.join(item.flavor_tags)}")

        # Dietary information
        if item.dietary_tags and len(item.dietary_tags) > 0:
            parts.append(f"dietary: {', '.join(item.dietary_tags)}")

        # Join with separator for clarity
        return " | ".join(filter(None, parts))

    async def generate_embedding(self, item: MenuItem) -> Optional[List[float]]:
        """
        Generate embedding vector for a menu item.

        Args:
            item: Menu item to embed

        Returns:
            Embedding vector as list of floats, or None if generation fails
        """
        try:
            text = self.build_item_text(item)
            if not text.strip():
                logger.warning(
                    "empty_embedding_text",
                    item_id=str(item.id),
                    item_name=item.name,
                )
                return None

            embedding = await embedding_service.embed(text)
            logger.debug(
                "embedding_generated",
                item_id=str(item.id),
                item_name=item.name,
                vector_dimension=len(embedding),
            )
            return embedding

        except Exception as e:
            logger.error(
                "embedding_generation_failed",
                item_id=str(item.id),
                item_name=item.name,
                error=str(e),
            )
            return None

    async def upsert_item_embedding(self, item: MenuItem) -> bool:
        """
        Generate and upsert a menu item's embedding to Qdrant.

        Args:
            item: Menu item to embed and store

        Returns:
            True if successful, False otherwise
        """
        if not vector_store.is_connected:
            logger.warning(
                "vector_store_not_connected",
                operation="upsert_item_embedding",
                item_id=str(item.id),
            )
            return False

        # Generate embedding
        embedding = await self.generate_embedding(item)
        if not embedding:
            return False

        # Prepare payload
        payload = {
            "menu_item_id": str(item.id),
            "brand_id": str(item.brand_id),
            "name": item.name,
            "category": item.category,
            "cuisine_type": item.cuisine_type,
            "dietary_tags": item.dietary_tags or [],
            "price": float(item.price) if item.price else None,
        }

        # Create point
        point = PointStruct(
            id=str(item.id),  # Use menu item UUID as point ID for easy lookup
            vector=embedding,
            payload=payload,
        )

        # Upsert to Qdrant
        success = await vector_store.upsert_points(
            collection_name=MENU_ITEM_EMBEDDINGS_COLLECTION,
            points=[point],
        )

        if success:
            # Update embedding_id in database
            item.embedding_id = str(item.id)
            await self.session.commit()
            logger.info(
                "item_embedding_upserted",
                item_id=str(item.id),
                item_name=item.name,
            )
        else:
            logger.error(
                "item_embedding_upsert_failed",
                item_id=str(item.id),
                item_name=item.name,
            )

        return success

    async def upsert_item_embedding_no_commit(self, item: MenuItem) -> bool:
        """
        Generate and upsert a menu item's embedding to Qdrant without committing.

        Use this when you want to embed items within a larger transaction.

        Args:
            item: Menu item to embed and store

        Returns:
            True if successful, False otherwise
        """
        if not vector_store.is_connected:
            logger.warning(
                "vector_store_not_connected",
                operation="upsert_item_embedding",
                item_id=str(item.id),
            )
            return False

        embedding = await self.generate_embedding(item)
        if not embedding:
            return False

        payload = {
            "menu_item_id": str(item.id),
            "brand_id": str(item.brand_id),
            "name": item.name,
            "category": item.category,
            "cuisine_type": item.cuisine_type,
            "dietary_tags": item.dietary_tags or [],
            "price": float(item.price) if item.price else None,
        }

        point = PointStruct(
            id=str(item.id),
            vector=embedding,
            payload=payload,
        )

        success = await vector_store.upsert_points(
            collection_name=MENU_ITEM_EMBEDDINGS_COLLECTION,
            points=[point],
        )

        if success:
            item.embedding_id = str(item.id)
            logger.info(
                "item_embedding_upserted",
                item_id=str(item.id),
                item_name=item.name,
            )
        else:
            logger.error(
                "item_embedding_upsert_failed",
                item_id=str(item.id),
                item_name=item.name,
            )
            item.embedding_id = None

        return success

    async def embed_all_items(
        self,
        brand_id: Optional[UUID] = None,
    ) -> dict:
        """
        Batch generate embeddings for all menu items.

        Args:
            brand_id: Optional filter to embed only items from a specific brand

        Returns:
            Dictionary with success/failure counts
        """
        # Build query
        query = select(MenuItem).options(selectinload(MenuItem.brand))
        if brand_id:
            query = query.where(MenuItem.brand_id == brand_id)

        result = await self.session.execute(query)
        items = result.scalars().all()

        if not items:
            logger.warning(
                "no_items_to_embed",
                brand_id=str(brand_id) if brand_id else None,
            )
            return {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "skipped": 0,
            }

        # Track results
        successful = 0
        failed = 0
        skipped = 0

        logger.info(
            "batch_embedding_started",
            total_items=len(items),
            brand_id=str(brand_id) if brand_id else None,
        )

        for item in items:
            # Skip items that are not available
            if not item.is_available:
                skipped += 1
                continue

            success = await self.upsert_item_embedding(item)
            if success:
                successful += 1
            else:
                failed += 1

        result_summary = {
            "total": len(items),
            "successful": successful,
            "failed": failed,
            "skipped": skipped,
        }

        logger.info(
            "batch_embedding_completed",
            **result_summary,
        )

        return result_summary

    async def delete_item_embedding(self, item_id: UUID) -> bool:
        """
        Delete an item's embedding from Qdrant.

        Args:
            item_id: Menu item UUID

        Returns:
            True if successful, False otherwise
        """
        if not vector_store.is_connected:
            logger.warning(
                "vector_store_not_connected",
                operation="delete_item_embedding",
                item_id=str(item_id),
            )
            return False

        from qdrant_client.models import PointIdsList

        success = await vector_store.delete_points(
            collection_name=MENU_ITEM_EMBEDDINGS_COLLECTION,
            points_selector=PointIdsList(points=[str(item_id)]),
        )

        if success:
            logger.info(
                "item_embedding_deleted",
                item_id=str(item_id),
            )
        else:
            logger.error(
                "item_embedding_delete_failed",
                item_id=str(item_id),
            )

        return success
