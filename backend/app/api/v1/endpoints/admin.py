"""
Admin endpoints for system operations.

These endpoints are for administrative tasks like batch embedding generation.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.intelligence.embedding_builder import EmbeddingBuilder

router = APIRouter(prefix="/admin")


@router.post("/embed-all-items")
async def embed_all_menu_items(
    brand_id: Optional[UUID] = Query(None, description="Optional: only embed items from this brand"),
    db: AsyncSession = Depends(get_db),
):
    """
    Batch generate embeddings for all menu items.

    This endpoint triggers embedding generation for all menu items in the system
    (or optionally for a specific brand). Useful for:
    - Initial setup when migrating existing menu data
    - Re-embedding all items after changing the embedding model
    - Regenerating embeddings after fixing item data

    Args:
        brand_id: Optional UUID to filter items by brand
        db: Database session

    Returns:
        Summary of embedding operation:
        - total: Total number of items processed
        - successful: Number of items successfully embedded
        - failed: Number of items that failed to embed
        - skipped: Number of items skipped (e.g., unavailable items)
    """
    builder = EmbeddingBuilder(db)
    result = await builder.embed_all_items(brand_id=brand_id)

    return {
        "message": "Batch embedding completed",
        "results": result,
    }
