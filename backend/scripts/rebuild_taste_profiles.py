"""
Script to batch update taste profiles for existing customers.

Run this after fixing the embedding lookup bug to rebuild all customer taste profiles.
"""

import asyncio
import sys

sys.path.insert(0, ".")

from uuid import UUID
from datetime import datetime, timezone
from typing import List, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import AsyncSessionLocal
from app.models.customer import Customer
from app.models.order import Order
from app.db.vector_store import vector_store
from app.services.intelligence.taste_profile_builder import TasteProfileBuilder
from app.services.intelligence.embedding_builder import EmbeddingBuilder


async def connect_vector_store() -> bool:
    """Connect to Qdrant vector store."""
    print("Connecting to Qdrant...")
    connected = await vector_store.connect()
    if connected:
        print("✓ Connected to Qdrant")
    else:
        print("✗ Failed to connect to Qdrant")
    return connected


async def get_customers_with_orders(session: AsyncSession) -> List[Customer]:
    """Get all customers who have placed orders."""
    result = await session.execute(
        select(Customer)
        .options(selectinload(Customer.orders))
        .where(Customer.orders.any())
    )
    return list(result.scalars().all())


async def check_menu_items_embeddings(session: AsyncSession) -> Dict:
    """Check how many menu items have embeddings."""
    from app.models.menu_item import MenuItem

    # Count total items
    result = await session.execute(select(MenuItem))
    total_items = len(result.scalars().all())

    # Count items with embeddings
    result = await session.execute(
        select(MenuItem).where(MenuItem.embedding_id.is_not(None))
    )
    items_with_embeddings = len(result.scalars().all())

    return {
        "total_items": total_items,
        "with_embeddings": items_with_embeddings,
        "without_embeddings": total_items - items_with_embeddings,
        "coverage_percent": (items_with_embeddings / total_items * 100)
        if total_items > 0
        else 0,
    }


async def build_missing_embeddings(session: AsyncSession) -> Dict:
    """Build embeddings for menu items that don't have them."""
    print("\nChecking for menu items without embeddings...")

    embedding_builder = EmbeddingBuilder(session)
    result = await embedding_builder.embed_all_items()

    print(f"  Total items: {result['total']}")
    print(f"  Successful: {result['successful']}")
    print(f"  Failed: {result['failed']}")
    print(f"  Skipped (not available): {result['skipped']}")

    return result


async def rebuild_customer_taste_profiles(session: AsyncSession) -> Dict:
    """Rebuild taste profiles for all customers with orders."""
    print("\nFetching customers with orders...")
    customers = await get_customers_with_orders(session)
    print(f"Found {len(customers)} customers with orders")

    builder = TasteProfileBuilder(session)

    results = {
        "total": len(customers),
        "success": 0,
        "insufficient_data": 0,
        "failed": 0,
        "errors": [],
    }

    for i, customer in enumerate(customers, 1):
        print(
            f"\n[{i}/{len(customers)}] Processing customer: {customer.email} ({customer.id})"
        )

        try:
            # Build taste profile
            result = await builder.build_taste_profile(customer.id)

            if result is None:
                results["failed"] += 1
                results["errors"].append(
                    {
                        "customer_id": str(customer.id),
                        "error": "Returned None (vector store not connected or customer not found)",
                    }
                )
                print(f"  ✗ Failed: Vector store not connected or customer not found")

            elif result.get("status") == "success":
                results["success"] += 1
                print(
                    f"  ✓ Success: {result.get('items_processed', 0)} items processed"
                )

            elif result.get("status") == "insufficient_data":
                results["insufficient_data"] += 1
                print(f"  ⚠ Insufficient data: {result.get('reason', 'unknown')}")

            else:
                results["failed"] += 1
                results["errors"].append(
                    {
                        "customer_id": str(customer.id),
                        "error": f"Unexpected status: {result.get('status')}",
                    }
                )
                print(f"  ✗ Failed: {result}")

        except Exception as e:
            results["failed"] += 1
            results["errors"].append({"customer_id": str(customer.id), "error": str(e)})
            print(f"  ✗ Error: {e}")

    return results


async def verify_taste_profiles() -> Dict:
    """Verify taste profiles were created in Qdrant."""
    print("\nVerifying taste profiles in Qdrant...")

    if not vector_store.is_connected:
        print("  ✗ Vector store not connected")
        return {"verified": False}

    try:
        # Get collection info
        from app.core.constants import CUSTOMER_TASTE_PROFILES_COLLECTION

        collections = await vector_store.client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if CUSTOMER_TASTE_PROFILES_COLLECTION not in collection_names:
            print(f"  ✗ Collection '{CUSTOMER_TASTE_PROFILES_COLLECTION}' not found")
            return {"verified": False}

        # Get collection stats
        collection_info = await vector_store.client.get_collection(
            CUSTOMER_TASTE_PROFILES_COLLECTION
        )

        print(f"  ✓ Collection found: {CUSTOMER_TASTE_PROFILES_COLLECTION}")
        print(f"    Points count: {collection_info.points_count}")

        return {"verified": True, "points_count": collection_info.points_count}

    except Exception as e:
        print(f"  ✗ Error verifying: {e}")
        return {"verified": False, "error": str(e)}


async def main():
    """Main function to run the taste profile update process."""
    print("=" * 70)
    print("TASTE PROFILE REBUILD SCRIPT")
    print("=" * 70)
    print()

    # Step 1: Connect to vector store
    if not await connect_vector_store():
        print("\n✗ Cannot proceed without Qdrant connection")
        sys.exit(1)

    async with AsyncSessionLocal() as session:
        # Step 2: Check current embedding coverage
        print("\n" + "-" * 70)
        print("STEP 1: Checking Menu Item Embedding Coverage")
        print("-" * 70)

        embedding_stats = await check_menu_items_embeddings(session)
        print(f"\n  Total menu items: {embedding_stats['total_items']}")
        print(f"  With embeddings: {embedding_stats['with_embeddings']}")
        print(f"  Without embeddings: {embedding_stats['without_embeddings']}")
        print(f"  Coverage: {embedding_stats['coverage_percent']:.1f}%")

        # Step 3: Build missing embeddings if needed
        if embedding_stats["without_embeddings"] > 0:
            print("\n" + "-" * 70)
            print("STEP 2: Building Missing Menu Item Embeddings")
            print("-" * 70)

            build_result = await build_missing_embeddings(session)

            if build_result["failed"] > 0:
                print(
                    f"\n⚠ Warning: {build_result['failed']} items failed to get embeddings"
                )
                response = input("\nContinue anyway? (y/n): ")
                if response.lower() != "y":
                    print("Aborted.")
                    return
        else:
            print("\n  ✓ All menu items have embeddings")

        # Step 4: Rebuild customer taste profiles
        print("\n" + "-" * 70)
        print("STEP 3: Rebuilding Customer Taste Profiles")
        print("-" * 70)

        response = input(
            "\nThis will rebuild taste profiles for ALL customers. Continue? (y/n): "
        )
        if response.lower() != "y":
            print("Aborted.")
            return

        results = await rebuild_customer_taste_profiles(session)

        # Step 5: Verify results
        print("\n" + "-" * 70)
        print("STEP 4: Verification")
        print("-" * 70)

        verification = await verify_taste_profiles()

        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"\nCustomers processed: {results['total']}")
        print(f"  ✓ Successful: {results['success']}")
        print(f"  ⚠ Insufficient data: {results['insufficient_data']}")
        print(f"  ✗ Failed: {results['failed']}")

        if verification.get("verified"):
            print(f"\nTaste profiles in Qdrant: {verification['points_count']}")

        if results["errors"]:
            print(f"\nErrors ({len(results['errors'])}):")
            for error in results["errors"][:5]:  # Show first 5
                print(f"  - Customer {error['customer_id'][:8]}...: {error['error']}")
            if len(results["errors"]) > 5:
                print(f"  ... and {len(results['errors']) - 5} more")

        print("\n" + "=" * 70)
        print("DONE")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
