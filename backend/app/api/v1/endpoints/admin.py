"""
Admin endpoints for system operations.

These endpoints are for administrative tasks like batch embedding generation
and taste profile rebuilding.
"""

from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.services.intelligence.embedding_builder import EmbeddingBuilder
from app.services.intelligence.taste_profile_builder import TasteProfileBuilder
from app.models.customer import Customer
from app.models.menu_item import MenuItem
from app.db.vector_store import vector_store
from app.core.constants import CUSTOMER_TASTE_PROFILES_COLLECTION

router = APIRouter(prefix="/admin")


@router.post("/embed-all-items")
async def embed_all_menu_items(
    brand_id: Optional[UUID] = Query(
        None, description="Optional: only embed items from this brand"
    ),
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


@router.post("/rebuild-taste-profiles")
async def rebuild_all_taste_profiles(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Rebuild taste profiles for all customers with orders.

    This endpoint starts a background task to rebuild taste profiles for all
    customers who have placed orders. This is useful after:
    - Fixing bugs in the taste profile builder
    - Updating the embedding model
    - Initial data migration

    The operation runs in the background and progress is logged.

    Returns:
        Status confirmation that the rebuild has started
    """
    background_tasks.add_task(_rebuild_all_profiles_task, db)

    return {
        "status": "started",
        "message": "Taste profile rebuild started in background",
        "note": "Check application logs for progress",
    }


@router.get("/taste-profile-stats")
async def get_taste_profile_stats(
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get statistics about taste profiles and embeddings.

    Returns current statistics about:
    - Menu items with/without embeddings
    - Customers with/without orders
    - Taste profiles stored in Qdrant

    Useful for monitoring system health and identifying data gaps.
    """
    # Get menu item stats
    result = await db.execute(select(MenuItem))
    total_items = len(result.scalars().all())

    result = await db.execute(
        select(MenuItem).where(MenuItem.embedding_id.is_not(None))
    )
    items_with_embeddings = len(result.scalars().all())

    # Get customer stats
    result = await db.execute(select(Customer))
    total_customers = len(result.scalars().all())

    result = await db.execute(select(Customer).where(Customer.orders.any()))
    customers_with_orders = len(result.scalars().all())

    # Get Qdrant stats
    taste_profiles_count = 0
    qdrant_connected = vector_store.is_connected

    if qdrant_connected:
        try:
            collections = await vector_store.client.get_collections()
            for col in collections.collections:
                if col.name == CUSTOMER_TASTE_PROFILES_COLLECTION:
                    info = await vector_store.client.get_collection(col.name)
                    taste_profiles_count = info.points_count
                    break
        except Exception:
            pass

    return {
        "menu_items": {
            "total": total_items,
            "with_embeddings": items_with_embeddings,
            "without_embeddings": total_items - items_with_embeddings,
            "coverage_percent": round(items_with_embeddings / total_items * 100, 1)
            if total_items > 0
            else 0,
        },
        "customers": {
            "total": total_customers,
            "with_orders": customers_with_orders,
            "without_orders": total_customers - customers_with_orders,
        },
        "taste_profiles": {
            "in_qdrant": taste_profiles_count,
            "estimated_missing": max(0, customers_with_orders - taste_profiles_count),
        },
        "qdrant_connected": qdrant_connected,
    }


@router.post("/rebuild-customer-profile/{customer_id}")
async def rebuild_single_customer_profile(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Rebuild taste profile for a single customer.

    Use this endpoint to rebuild a specific customer's taste profile,
    for example when debugging issues or after data corrections.

    Args:
        customer_id: UUID of the customer to rebuild

    Returns:
        Result of the rebuild operation with status and metadata
    """
    builder = TasteProfileBuilder(db)
    result = await builder.build_taste_profile(customer_id)

    if result is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to build taste profile. Check that Qdrant is connected and customer exists.",
        )

    return {"customer_id": str(customer_id), **result}


# Background task functions
async def _rebuild_all_profiles_task(db: AsyncSession):
    """Background task to rebuild all taste profiles."""
    import structlog

    logger = structlog.get_logger(__name__)

    logger.info("background_rebuild_taste_profiles_started")

    try:
        # Get all customers with orders
        result = await db.execute(
            select(Customer)
            .options(selectinload(Customer.orders))
            .where(Customer.orders.any())
        )
        customers = result.scalars().all()

        builder = TasteProfileBuilder(db)
        success_count = 0
        failed_count = 0

        for customer in customers:
            try:
                result = await builder.build_taste_profile(customer.id)
                if result and result.get("status") == "success":
                    success_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(
                    "rebuild_profile_failed", customer_id=str(customer.id), error=str(e)
                )
                failed_count += 1

        logger.info(
            "background_rebuild_taste_profiles_completed",
            total=len(customers),
            success=success_count,
            failed=failed_count,
        )

    except Exception as e:
        logger.error("background_rebuild_taste_profiles_error", error=str(e))
