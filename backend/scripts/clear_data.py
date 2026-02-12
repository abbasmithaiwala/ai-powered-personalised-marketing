"""
Script to clear all data from Qdrant and the database for fresh testing.

WARNING: This will DELETE all data!
"""

import asyncio
import sys

sys.path.insert(0, ".")

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from app.db.session import engine
from app.db.vector_store import vector_store
from app.core.config import settings
from app.core.constants import (
    MENU_ITEM_EMBEDDINGS_COLLECTION,
    CUSTOMER_TASTE_PROFILES_COLLECTION,
)


AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def clear_qdrant():
    """Clear all Qdrant collections."""
    print("=" * 70)
    print("CLEARING QDRANT DATA")
    print("=" * 70)

    connected = await vector_store.connect()
    if not connected:
        print("✗ Failed to connect to Qdrant")
        return False

    # Collections to clear
    collections_to_clear = [
        MENU_ITEM_EMBEDDINGS_COLLECTION,
        CUSTOMER_TASTE_PROFILES_COLLECTION,
        "popular_items",
        "customer_preferences",
    ]

    for collection in collections_to_clear:
        try:
            # Check if collection exists
            collections = await vector_store.client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if collection in collection_names:
                # Delete all points in the collection
                await vector_store.client.delete_collection(collection)
                print(f"✓ Deleted collection: {collection}")
            else:
                print(f"  Collection not found (skipping): {collection}")
        except Exception as e:
            print(f"  Error clearing {collection}: {e}")

    print("\n✓ Qdrant data cleared!")

    # Recreate collections immediately so they're available for new data
    print("\n" + "-" * 70)
    print("RECREATING QDRANT COLLECTIONS")
    print("-" * 70)
    try:
        await vector_store.ensure_collections()
        print("✓ Collections recreated successfully")
        print("\n✅ You can now upload CSV files immediately - no restart needed!")
    except Exception as e:
        print(f"\n⚠️  Warning: Failed to recreate collections: {e}")
        print("   You may need to restart the backend:")
        print("   docker compose restart backend")

    return True


async def clear_database(db: AsyncSession):
    """Clear all database tables."""
    print("\n" + "=" * 70)
    print("CLEARING DATABASE DATA")
    print("=" * 70)

    # Order matters due to foreign key constraints
    tables_to_clear = [
        "campaign_recipients",
        "campaigns",
        "ingestion_jobs",
        "order_items",
        "orders",
        "customer_preferences",
        "menu_items",
        "customers",
        "brands",
    ]

    for table in tables_to_clear:
        try:
            await db.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
            print(f"✓ Truncated table: {table}")
        except Exception as e:
            print(f"  Note: {table} - table may not exist")

    await db.commit()
    print("\n✓ All database tables cleared!")


async def verify_cleared_data(db: AsyncSession):
    """Verify that data has been cleared."""
    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)

    # Check Qdrant
    print("\nQdrant collections:")
    try:
        collections = await vector_store.client.get_collections()
        for collection in collections.collections:
            info = await vector_store.client.get_collection(collection.name)
            print(f"  {collection.name}: {info.points_count} points")
    except Exception as e:
        print(f"  Error checking Qdrant: {e}")

    # Check database tables
    print("\nDatabase tables:")

    tables = [
        ("brands", "SELECT COUNT(*) FROM brands"),
        ("customers", "SELECT COUNT(*) FROM customers"),
        ("menu_items", "SELECT COUNT(*) FROM menu_items"),
        ("orders", "SELECT COUNT(*) FROM orders"),
        ("order_items", "SELECT COUNT(*) FROM order_items"),
        ("campaigns", "SELECT COUNT(*) FROM campaigns"),
        ("campaign_recipients", "SELECT COUNT(*) FROM campaign_recipients"),
        ("ingestion_jobs", "SELECT COUNT(*) FROM ingestion_jobs"),
        (
            "menu_items with embeddings",
            "SELECT COUNT(*) FROM menu_items WHERE embedding_id IS NOT NULL",
        ),
    ]

    for name, query in tables:
        try:
            result = await db.execute(text(query))
            count = result.scalar()
            print(f"  {name}: {count}")
        except Exception as e:
            print(f"  {name}: Error - {e}")


async def main():
    """Main function to clear all data."""
    print("\n" + "=" * 70)
    print("⚠️  WARNING: This will DELETE ALL DATA from Qdrant and Database! ⚠️")
    print("=" * 70)
    print("\nThis will clear:")
    print("  - All Qdrant collections (embeddings, taste profiles, etc.)")
    print("  - All orders and order_items")
    print("  - All taste profiles and customer preferences")
    print("  - All menu items")
    print("  - All customers")
    print("  - All brands")
    print("=" * 70)

    response = input(
        "\nAre you sure you want to continue? (type 'DELETE' to confirm): "
    )
    if response != "DELETE":
        print("\nAborted. No data was deleted.")
        return

    # Clear Qdrant
    success = await clear_qdrant()
    if not success:
        print("Failed to clear Qdrant. Aborting database clear.")
        return

    # Clear database
    async with AsyncSessionLocal() as db:
        await clear_database(db)

    # Verify
    async with AsyncSessionLocal() as db:
        await verify_cleared_data(db)

    print("\n" + "=" * 70)
    print("✅ ALL DATA HAS BEEN CLEARED SUCCESSFULLY!")
    print("=" * 70)
    print("\n📝 Note: Qdrant collections have been recreated automatically.")
    print("   You can now upload CSV files and taste profiles will be")
    print("   built correctly without restarting the backend.")


if __name__ == "__main__":
    asyncio.run(main())
