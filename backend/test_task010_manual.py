#!/usr/bin/env python3
"""
Manual integration test for TASK-010: Menu Item Vector Embeddings

Tests the full embedding workflow:
1. Create menu item (triggers embedding generation)
2. Update menu item (re-triggers if content changed)
3. Batch embed all items via admin endpoint
4. Verify embeddings in Qdrant

Run with: python test_task010_manual.py
"""

import asyncio
import sys
from uuid import uuid4

import httpx
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "dev-key-123"  # From .env

HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json",
}


async def test_embedding_workflow():
    """Test the complete menu item embedding workflow."""

    async with httpx.AsyncClient(timeout=30.0) as client:

        # Step 1: Create a brand first
        logger.info("step_1_creating_brand")
        brand_data = {
            "name": f"Embedding Test Restaurant {uuid4().hex[:8]}",
            "slug": f"embedding-test-{uuid4().hex[:8]}",
            "cuisine_type": "Italian",
            "is_active": True,
        }

        response = await client.post(
            f"{BASE_URL}/brands",
            json=brand_data,
            headers=HEADERS,
        )
        assert response.status_code == 201, f"Failed to create brand: {response.text}"
        brand = response.json()
        brand_id = brand["id"]
        logger.info("brand_created", brand_id=brand_id)

        # Step 2: Create a menu item (should trigger embedding)
        logger.info("step_2_creating_menu_item_with_embedding")
        item_data = {
            "name": "Truffle Risotto",
            "brand_id": brand_id,
            "description": "Creamy arborio rice with black truffle, parmesan, and white wine",
            "category": "Mains",
            "cuisine_type": "Italian",
            "price": 24.50,
            "dietary_tags": ["vegetarian", "gluten-free"],
            "flavor_tags": ["rich", "umami", "earthy", "creamy"],
            "is_available": True,
        }

        response = await client.post(
            f"{BASE_URL}/menu-items",
            json=item_data,
            headers=HEADERS,
        )
        assert response.status_code == 201, f"Failed to create item: {response.text}"
        item = response.json()
        item_id = item["id"]
        logger.info("menu_item_created", item_id=item_id, embedding_id=item.get("embedding_id"))

        # Give it a moment for embedding to be generated
        await asyncio.sleep(2)

        # Verify item was created and embedding_id set
        response = await client.get(
            f"{BASE_URL}/menu-items/{item_id}",
            headers=HEADERS,
        )
        assert response.status_code == 200
        item = response.json()
        assert item["embedding_id"] is not None, "Embedding ID should be set after creation"
        logger.info("embedding_id_verified", embedding_id=item["embedding_id"])

        # Step 3: Update item content (should re-trigger embedding)
        logger.info("step_3_updating_item_content")
        update_data = {
            "description": "Luxurious arborio rice with premium black truffle, aged parmesan, and Italian white wine - a true delicacy",
            "flavor_tags": ["rich", "umami", "earthy", "creamy", "luxurious"],
        }

        response = await client.put(
            f"{BASE_URL}/menu-items/{item_id}",
            json=update_data,
            headers=HEADERS,
        )
        assert response.status_code == 200, f"Failed to update item: {response.text}"
        logger.info("item_updated_embedding_regenerated")

        await asyncio.sleep(1)

        # Step 4: Create a few more items for batch test
        logger.info("step_4_creating_additional_items")
        additional_items = [
            {
                "name": "Margherita Pizza",
                "brand_id": brand_id,
                "description": "Classic Neapolitan pizza with San Marzano tomatoes, buffalo mozzarella, and fresh basil",
                "category": "Mains",
                "cuisine_type": "Italian",
                "price": 14.00,
                "dietary_tags": ["vegetarian"],
                "flavor_tags": ["savory", "cheesy", "herby"],
                "is_available": True,
            },
            {
                "name": "Tiramisu",
                "brand_id": brand_id,
                "description": "Traditional Italian dessert with espresso-soaked ladyfingers, mascarpone, and cocoa",
                "category": "Desserts",
                "cuisine_type": "Italian",
                "price": 8.50,
                "dietary_tags": ["vegetarian"],
                "flavor_tags": ["sweet", "creamy", "coffee"],
                "is_available": True,
            },
        ]

        created_item_ids = [item_id]
        for item_data in additional_items:
            response = await client.post(
                f"{BASE_URL}/menu-items",
                json=item_data,
                headers=HEADERS,
            )
            assert response.status_code == 201
            created_item_ids.append(response.json()["id"])

        logger.info("additional_items_created", count=len(additional_items))

        await asyncio.sleep(2)

        # Step 5: Test batch embedding endpoint
        logger.info("step_5_testing_batch_embed_endpoint")
        response = await client.post(
            f"{BASE_URL}/admin/embed-all-items",
            params={"brand_id": brand_id},
            headers=HEADERS,
        )
        assert response.status_code == 200, f"Batch embed failed: {response.text}"
        batch_result = response.json()
        logger.info("batch_embedding_completed", results=batch_result["results"])

        # Verify results
        results = batch_result["results"]
        assert results["total"] >= 3, "Should have at least 3 items"
        assert results["successful"] > 0, "Should have successfully embedded items"

        # Step 6: Verify all items have embeddings
        logger.info("step_6_verifying_all_embeddings")
        for item_id in created_item_ids:
            response = await client.get(
                f"{BASE_URL}/menu-items/{item_id}",
                headers=HEADERS,
            )
            assert response.status_code == 200
            item = response.json()
            assert item["embedding_id"] is not None, f"Item {item_id} should have embedding_id"
            logger.info("item_embedding_verified", item_id=item_id, name=item["name"])

        # Step 7: Test with unavailable item (should be skipped in batch)
        logger.info("step_7_testing_unavailable_item_skip")
        response = await client.post(
            f"{BASE_URL}/menu-items",
            json={
                "name": "Unavailable Dish",
                "brand_id": brand_id,
                "description": "This item is not available",
                "category": "Mains",
                "cuisine_type": "Italian",
                "price": 10.00,
                "is_available": False,
            },
            headers=HEADERS,
        )
        assert response.status_code == 201
        unavailable_id = response.json()["id"]

        # Run batch again
        response = await client.post(
            f"{BASE_URL}/admin/embed-all-items",
            params={"brand_id": brand_id},
            headers=HEADERS,
        )
        assert response.status_code == 200
        results = response.json()["results"]
        assert results["skipped"] >= 1, "Should have skipped at least one unavailable item"
        logger.info("unavailable_item_skip_verified", skipped_count=results["skipped"])

        # Cleanup
        logger.info("cleanup_deleting_test_data")
        for item_id in created_item_ids + [unavailable_id]:
            await client.delete(f"{BASE_URL}/menu-items/{item_id}", headers=HEADERS)

        await client.delete(f"{BASE_URL}/brands/{brand_id}", headers=HEADERS)
        logger.info("cleanup_completed")

        logger.info("✅ ALL TESTS PASSED!")
        return True


async def check_prerequisites():
    """Check that required services are running."""
    logger.info("checking_prerequisites")

    async with httpx.AsyncClient(timeout=5.0) as client:
        # Check API is running
        try:
            response = await client.get(f"{BASE_URL}/health")
            assert response.status_code == 200
            logger.info("api_health_check_passed")
        except Exception as e:
            logger.error("api_not_running", error=str(e))
            logger.error("Please start the API with: uvicorn app.main:app --reload")
            return False

        # Check Qdrant is accessible (via health endpoint should validate this)
        health = response.json()
        logger.info("services_ready", health=health)

    return True


async def main():
    """Main test runner."""
    logger.info("🚀 Starting TASK-010 Integration Tests")

    # Check prerequisites
    if not await check_prerequisites():
        sys.exit(1)

    # Run tests
    try:
        await test_embedding_workflow()
        logger.info("✅ All integration tests passed!")
        return 0
    except AssertionError as e:
        logger.error("❌ Test failed", error=str(e))
        return 1
    except Exception as e:
        logger.error("❌ Unexpected error", error=str(e), exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
