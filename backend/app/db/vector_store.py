"""
Qdrant vector store client and collection management.
"""

import structlog
from typing import Optional, List, Dict, Any
from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from qdrant_client.http.exceptions import UnexpectedResponse

from app.core.config import settings
from app.core.constants import (
    MENU_ITEM_EMBEDDINGS_COLLECTION,
    CUSTOMER_TASTE_PROFILES_COLLECTION,
    VECTOR_DIMENSION,
    VECTOR_DISTANCE,
)

logger = structlog.get_logger(__name__)


class VectorStore:
    """
    Singleton wrapper for Qdrant client with collection management.
    """

    def __init__(self):
        self.client: Optional[AsyncQdrantClient] = None
        self._connected = False

    async def connect(self) -> bool:
        """
        Initialize connection to Qdrant and create collections if needed.

        Returns:
            bool: True if connected successfully, False otherwise
        """
        try:
            self.client = AsyncQdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                timeout=10.0,
            )

            # Test connection
            await self.client.get_collections()
            self._connected = True
            logger.info(
                "qdrant_connected",
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
            )

            # Create collections if they don't exist
            await self.ensure_collections()

            return True

        except Exception as e:
            logger.warning(
                "qdrant_connection_failed",
                error=str(e),
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
            )
            self._connected = False
            return False

    async def ensure_collections(self):
        """
        Create collections if they don't exist (idempotent).
        Public method that can be called from external scripts.
        """
        if not self.client:
            return

        collections = [
            {
                "name": MENU_ITEM_EMBEDDINGS_COLLECTION,
                "description": "Menu item embeddings for semantic search",
            },
            {
                "name": CUSTOMER_TASTE_PROFILES_COLLECTION,
                "description": "Customer taste profile vectors",
            },
        ]

        for collection_config in collections:
            try:
                await self._create_collection_if_not_exists(collection_config["name"])
                logger.info(
                    "qdrant_collection_ready",
                    collection=collection_config["name"],
                )
            except Exception as e:
                logger.error(
                    "qdrant_collection_creation_failed",
                    collection=collection_config["name"],
                    error=str(e),
                )

    async def _create_collection_if_not_exists(self, collection_name: str):
        """
        Create a collection if it doesn't already exist.

        Args:
            collection_name: Name of the collection to create
        """
        if not self.client:
            return

        try:
            # Check if collection exists
            collections = await self.client.get_collections()
            existing_names = [col.name for col in collections.collections]

            if collection_name not in existing_names:
                # Create collection
                await self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=VECTOR_DIMENSION,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(
                    "qdrant_collection_created",
                    collection=collection_name,
                    dimension=VECTOR_DIMENSION,
                )
            else:
                logger.debug(
                    "qdrant_collection_exists",
                    collection=collection_name,
                )

        except UnexpectedResponse as e:
            # Collection might already exist from a concurrent request
            if "already exists" in str(e).lower():
                logger.debug(
                    "qdrant_collection_already_exists",
                    collection=collection_name,
                )
            else:
                raise

    async def upsert_points(
        self,
        collection_name: str,
        points: List[PointStruct],
    ) -> bool:
        """
        Upsert points into a collection.

        Args:
            collection_name: Name of the collection
            points: List of points to upsert

        Returns:
            bool: True if successful, False otherwise
        """
        if not self._connected or not self.client:
            logger.warning("qdrant_not_connected", operation="upsert")
            return False

        try:
            await self.client.upsert(
                collection_name=collection_name,
                points=points,
            )
            logger.debug(
                "qdrant_points_upserted",
                collection=collection_name,
                count=len(points),
            )
            return True

        except Exception as e:
            logger.error(
                "qdrant_upsert_failed",
                collection=collection_name,
                error=str(e),
            )
            return False

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        query_filter: Optional[Filter] = None,
    ) -> List[Any]:
        """
        Search for similar vectors in a collection.

        Args:
            collection_name: Name of the collection to search
            query_vector: Query vector
            limit: Maximum number of results to return
            query_filter: Optional filter to apply

        Returns:
            List of search results
        """
        if not self._connected or not self.client:
            logger.warning("qdrant_not_connected", operation="search")
            return []

        try:
            # Use query_points for AsyncQdrantClient
            from qdrant_client.models import QueryRequest

            results = await self.client.query_points(
                collection_name=collection_name,
                query=query_vector,
                limit=limit,
                query_filter=query_filter,
            )
            logger.debug(
                "qdrant_search_completed",
                collection=collection_name,
                results_count=len(results.points) if results.points else 0,
            )
            return results.points if results.points else []

        except Exception as e:
            logger.error(
                "qdrant_search_failed",
                collection=collection_name,
                error=str(e),
            )
            return []

    async def delete_points(
        self,
        collection_name: str,
        points_selector: Any,
    ) -> bool:
        """
        Delete points from a collection.

        Args:
            collection_name: Name of the collection
            points_selector: Point IDs or filter to select points

        Returns:
            bool: True if successful, False otherwise
        """
        if not self._connected or not self.client:
            logger.warning("qdrant_not_connected", operation="delete")
            return False

        try:
            await self.client.delete(
                collection_name=collection_name,
                points_selector=points_selector,
            )
            logger.debug(
                "qdrant_points_deleted",
                collection=collection_name,
            )
            return True

        except Exception as e:
            logger.error(
                "qdrant_delete_failed",
                collection=collection_name,
                error=str(e),
            )
            return False

    async def get_point(
        self,
        collection_name: str,
        point_id: str,
    ) -> Optional[Any]:
        """
        Retrieve a specific point by ID.

        Args:
            collection_name: Name of the collection
            point_id: ID of the point to retrieve

        Returns:
            Point data if found, None otherwise
        """
        if not self._connected or not self.client:
            logger.warning("qdrant_not_connected", operation="get_point")
            return None

        try:
            result = await self.client.retrieve(
                collection_name=collection_name,
                ids=[point_id],
                with_vectors=True,  # IMPORTANT: Must include vectors!
            )
            if result:
                return result[0]
            return None

        except Exception as e:
            logger.error(
                "qdrant_get_point_failed",
                collection=collection_name,
                point_id=point_id,
                error=str(e),
            )
            return None

    async def close(self):
        """Close the Qdrant client connection."""
        if self.client:
            await self.client.close()
            self._connected = False
            logger.info("qdrant_connection_closed")

    @property
    def is_connected(self) -> bool:
        """Check if connected to Qdrant."""
        return self._connected


# Singleton instance
vector_store = VectorStore()
