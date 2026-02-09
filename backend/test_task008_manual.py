"""
Manual test script for TASK-008 — Brand & Menu Catalog API.

This script tests the CRUD operations for brands and menu items.

Usage:
    python test_task008_manual.py
"""

import asyncio
import httpx
from decimal import Decimal

BASE_URL = "http://localhost:8001/api/v1"


async def test_brands():
    """Test brand CRUD operations."""
    print("\n=== Testing Brand API ===\n")

    async with httpx.AsyncClient() as client:
        # Test 1: Create brands
        print("1. Creating brands...")
        brands_data = [
            {
                "name": "Mama's Kitchen",
                "slug": "mamas-kitchen",
                "cuisine_type": "Italian",
                "is_active": True
            },
            {
                "name": "Spice Route",
                "slug": "spice-route",
                "cuisine_type": "Indian",
                "is_active": True
            },
            {
                "name": "Tokyo Express",
                "slug": "tokyo-express",
                "cuisine_type": "Japanese",
                "is_active": True
            }
        ]

        created_brands = []
        for brand_data in brands_data:
            response = await client.post(f"{BASE_URL}/brands", json=brand_data)
            if response.status_code == 201:
                brand = response.json()
                created_brands.append(brand)
                print(f"✓ Created brand: {brand['name']} (ID: {brand['id']})")
            else:
                print(f"✗ Failed to create brand {brand_data['name']}: {response.status_code} - {response.text}")

        # Test 2: List all brands
        print("\n2. Listing all brands...")
        response = await client.get(f"{BASE_URL}/brands")
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Total brands: {result['total']}")
            print(f"  Page {result['page']}/{result['pages']} (page_size: {result['page_size']})")
            for brand in result['items']:
                print(f"  - {brand['name']} ({brand['cuisine_type']})")
        else:
            print(f"✗ Failed to list brands: {response.status_code}")

        if not created_brands:
            print("\n⚠️  No brands created, skipping remaining tests")
            return None

        # Test 3: Get brand by ID
        print("\n3. Getting brand by ID...")
        brand_id = created_brands[0]['id']
        response = await client.get(f"{BASE_URL}/brands/{brand_id}")
        if response.status_code == 200:
            brand = response.json()
            print(f"✓ Retrieved brand: {brand['name']}")
        else:
            print(f"✗ Failed to get brand: {response.status_code}")

        # Test 4: Update brand
        print("\n4. Updating brand...")
        update_data = {
            "name": "Mama's Italian Kitchen",
            "cuisine_type": "Italian & Mediterranean"
        }
        response = await client.put(f"{BASE_URL}/brands/{brand_id}", json=update_data)
        if response.status_code == 200:
            brand = response.json()
            print(f"✓ Updated brand: {brand['name']} ({brand['cuisine_type']})")
        else:
            print(f"✗ Failed to update brand: {response.status_code}")

        # Test 5: Delete brand (soft delete)
        print("\n5. Soft deleting a brand...")
        delete_brand_id = created_brands[-1]['id'] if len(created_brands) > 1 else brand_id
        response = await client.delete(f"{BASE_URL}/brands/{delete_brand_id}")
        if response.status_code == 204:
            print(f"✓ Soft deleted brand (ID: {delete_brand_id})")
        else:
            print(f"✗ Failed to delete brand: {response.status_code}")

        # Verify soft delete
        response = await client.get(f"{BASE_URL}/brands/{delete_brand_id}")
        if response.status_code == 200:
            brand = response.json()
            print(f"  Brand still exists with is_active={brand['is_active']}")

        return created_brands[0] if created_brands else None


async def test_menu_items(brand_id: str):
    """Test menu item CRUD operations."""
    print("\n=== Testing Menu Item API ===\n")

    async with httpx.AsyncClient() as client:
        # Test 1: Create menu items
        print("1. Creating menu items...")
        items_data = [
            {
                "brand_id": brand_id,
                "name": "Margherita Pizza",
                "description": "Classic pizza with tomato, mozzarella, and basil",
                "category": "Main",
                "cuisine_type": "Italian",
                "price": "12.50",
                "dietary_tags": ["vegetarian"],
                "flavor_tags": ["savory", "cheesy"],
                "is_available": True
            },
            {
                "brand_id": brand_id,
                "name": "Spaghetti Carbonara",
                "description": "Pasta with eggs, cheese, and pancetta",
                "category": "Main",
                "cuisine_type": "Italian",
                "price": "15.00",
                "dietary_tags": [],
                "flavor_tags": ["savory", "creamy"],
                "is_available": True
            },
            {
                "brand_id": brand_id,
                "name": "Tiramisu",
                "description": "Classic Italian dessert with coffee and mascarpone",
                "category": "Dessert",
                "cuisine_type": "Italian",
                "price": "8.00",
                "dietary_tags": ["vegetarian"],
                "flavor_tags": ["sweet", "coffee"],
                "is_available": True
            }
        ]

        created_items = []
        for item_data in items_data:
            response = await client.post(f"{BASE_URL}/menu-items", json=item_data)
            if response.status_code == 201:
                item = response.json()
                created_items.append(item)
                print(f"✓ Created item: {item['name']} (${item['price']})")
            else:
                print(f"✗ Failed to create item {item_data['name']}: {response.status_code} - {response.text}")

        # Test 2: List all menu items
        print("\n2. Listing all menu items...")
        response = await client.get(f"{BASE_URL}/menu-items")
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Total items: {result['total']}")
            for item in result['items']:
                print(f"  - {item['name']} (${item['price']}) - {item['category']}")
        else:
            print(f"✗ Failed to list items: {response.status_code}")

        # Test 3: Filter by brand
        print(f"\n3. Filtering items by brand_id={brand_id}...")
        response = await client.get(f"{BASE_URL}/menu-items?brand_id={brand_id}")
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Found {result['total']} items for this brand")
        else:
            print(f"✗ Failed to filter by brand: {response.status_code}")

        # Test 4: Filter by category
        print("\n4. Filtering items by category=Main...")
        response = await client.get(f"{BASE_URL}/menu-items?category=Main")
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Found {result['total']} main dishes")
        else:
            print(f"✗ Failed to filter by category: {response.status_code}")

        # Test 5: Filter by dietary tag
        print("\n5. Filtering items by dietary_tag=vegetarian...")
        response = await client.get(f"{BASE_URL}/menu-items?dietary_tag=vegetarian")
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Found {result['total']} vegetarian items")
        else:
            print(f"✗ Failed to filter by dietary tag: {response.status_code}")

        if not created_items:
            print("\n⚠️  No items created, skipping remaining tests")
            return

        # Test 6: Get item by ID
        print("\n6. Getting menu item by ID...")
        item_id = created_items[0]['id']
        response = await client.get(f"{BASE_URL}/menu-items/{item_id}")
        if response.status_code == 200:
            item = response.json()
            print(f"✓ Retrieved item: {item['name']}")
        else:
            print(f"✗ Failed to get item: {response.status_code}")

        # Test 7: Update menu item
        print("\n7. Updating menu item...")
        update_data = {
            "price": "13.99",
            "description": "Classic Neapolitan pizza with San Marzano tomatoes, buffalo mozzarella, and fresh basil"
        }
        response = await client.put(f"{BASE_URL}/menu-items/{item_id}", json=update_data)
        if response.status_code == 200:
            item = response.json()
            print(f"✓ Updated item: {item['name']} - New price: ${item['price']}")
            print(f"  New description: {item['description'][:60]}...")
        else:
            print(f"✗ Failed to update item: {response.status_code}")

        # Test 8: Delete menu item (soft delete)
        print("\n8. Soft deleting a menu item...")
        delete_item_id = created_items[-1]['id']
        response = await client.delete(f"{BASE_URL}/menu-items/{delete_item_id}")
        if response.status_code == 204:
            print(f"✓ Soft deleted item (ID: {delete_item_id})")
        else:
            print(f"✗ Failed to delete item: {response.status_code}")

        # Verify soft delete
        response = await client.get(f"{BASE_URL}/menu-items/{delete_item_id}")
        if response.status_code == 200:
            item = response.json()
            print(f"  Item still exists with is_available={item['is_available']}")


async def test_pagination():
    """Test pagination functionality."""
    print("\n=== Testing Pagination ===\n")

    async with httpx.AsyncClient() as client:
        # Create multiple brands for pagination testing
        print("1. Creating 30 test brands for pagination...")
        for i in range(30):
            brand_data = {
                "name": f"Test Restaurant {i+1}",
                "slug": f"test-restaurant-{i+1}",
                "cuisine_type": "Test",
                "is_active": True
            }
            await client.post(f"{BASE_URL}/brands", json=brand_data)
        print("✓ Created 30 test brands")

        # Test pagination
        print("\n2. Testing pagination (page_size=10)...")
        response = await client.get(f"{BASE_URL}/brands?page=1&page_size=10")
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Page 1: {len(result['items'])} items")
            print(f"  Total: {result['total']}, Pages: {result['pages']}")

        response = await client.get(f"{BASE_URL}/brands?page=2&page_size=10")
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Page 2: {len(result['items'])} items")

        response = await client.get(f"{BASE_URL}/brands?page=3&page_size=10")
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Page 3: {len(result['items'])} items")


async def test_error_cases():
    """Test error handling."""
    print("\n=== Testing Error Cases ===\n")

    async with httpx.AsyncClient() as client:
        # Test 1: Get non-existent brand
        print("1. Getting non-existent brand...")
        response = await client.get(f"{BASE_URL}/brands/00000000-0000-0000-0000-000000000000")
        if response.status_code == 404:
            print("✓ Correctly returned 404 for non-existent brand")
        else:
            print(f"✗ Expected 404, got {response.status_code}")

        # Test 2: Create item with non-existent brand
        print("\n2. Creating item with non-existent brand...")
        item_data = {
            "brand_id": "00000000-0000-0000-0000-000000000000",
            "name": "Test Item",
            "price": "10.00",
            "is_available": True
        }
        response = await client.post(f"{BASE_URL}/menu-items", json=item_data)
        if response.status_code == 404:
            print("✓ Correctly returned 404 for non-existent brand")
        else:
            print(f"✗ Expected 404, got {response.status_code}")

        # Test 3: Invalid pagination parameters
        print("\n3. Testing invalid pagination (page=0)...")
        response = await client.get(f"{BASE_URL}/brands?page=0")
        if response.status_code == 422:
            print("✓ Correctly returned 422 for invalid page number")
        else:
            print(f"✗ Expected 422, got {response.status_code}")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("TASK-008 Manual Test Suite")
    print("Brand & Menu Catalog API")
    print("=" * 60)

    try:
        # Test brands
        brand = await test_brands()

        # Test menu items (if we have a brand)
        if brand:
            await test_menu_items(brand['id'])

        # Test pagination
        await test_pagination()

        # Test error cases
        await test_error_cases()

        print("\n" + "=" * 60)
        print("✓ All tests completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
