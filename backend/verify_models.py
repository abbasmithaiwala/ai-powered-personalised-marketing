#!/usr/bin/env python3
"""
Verification script for TASK-003: Database Models & Alembic Migrations

This script verifies:
1. All models can be imported
2. All relationships are properly defined
3. All tables are registered in Base.metadata
4. Migration file exists
"""

import sys
from pathlib import Path

def verify_models():
    """Verify all models are correctly defined"""
    print("=" * 60)
    print("TASK-003 Verification Script")
    print("=" * 60)
    print()

    # Test 1: Import all models
    print("✓ Test 1: Importing models...")
    try:
        from app.models import (
            Base,
            Brand,
            MenuItem,
            Customer,
            Order,
            OrderItem,
            CustomerPreference,
            IngestionJob,
        )
        print("  ✅ All models imported successfully")
    except ImportError as e:
        print(f"  ❌ Failed to import models: {e}")
        return False

    # Test 2: Check tables in metadata
    print("\n✓ Test 2: Checking tables in Base.metadata...")
    expected_tables = {
        'brands',
        'menu_items',
        'customers',
        'orders',
        'order_items',
        'customer_preferences',
        'ingestion_jobs',
    }
    actual_tables = set(Base.metadata.tables.keys())

    if actual_tables == expected_tables:
        print(f"  ✅ All {len(expected_tables)} tables registered")
        for table in sorted(actual_tables):
            print(f"     - {table}")
    else:
        print(f"  ❌ Table mismatch!")
        print(f"     Expected: {expected_tables}")
        print(f"     Actual: {actual_tables}")
        return False

    # Test 3: Check relationships
    print("\n✓ Test 3: Checking model relationships...")

    # Brand relationships
    assert hasattr(Brand, 'menu_items'), "Brand missing menu_items relationship"
    assert hasattr(Brand, 'orders'), "Brand missing orders relationship"

    # Customer relationships
    assert hasattr(Customer, 'orders'), "Customer missing orders relationship"
    assert hasattr(Customer, 'preference'), "Customer missing preference relationship"

    # Order relationships
    assert hasattr(Order, 'customer'), "Order missing customer relationship"
    assert hasattr(Order, 'brand'), "Order missing brand relationship"
    assert hasattr(Order, 'order_items'), "Order missing order_items relationship"

    # MenuItem relationships
    assert hasattr(MenuItem, 'brand'), "MenuItem missing brand relationship"
    assert hasattr(MenuItem, 'order_items'), "MenuItem missing order_items relationship"

    # OrderItem relationships
    assert hasattr(OrderItem, 'order'), "OrderItem missing order relationship"
    assert hasattr(OrderItem, 'menu_item'), "OrderItem missing menu_item relationship"

    # CustomerPreference relationships
    assert hasattr(CustomerPreference, 'customer'), "CustomerPreference missing customer relationship"

    print("  ✅ All relationships defined correctly")

    # Test 4: Check migration file exists
    print("\n✓ Test 4: Checking migration file...")
    migration_file = Path(__file__).parent / "alembic" / "versions" / "001_initial_schema.py"
    if migration_file.exists():
        print(f"  ✅ Migration file exists: {migration_file.name}")
    else:
        print(f"  ❌ Migration file not found: {migration_file}")
        return False

    # Test 5: Check alembic.ini exists
    print("\n✓ Test 5: Checking Alembic configuration...")
    alembic_ini = Path(__file__).parent / "alembic.ini"
    if alembic_ini.exists():
        print(f"  ✅ alembic.ini exists")
    else:
        print(f"  ❌ alembic.ini not found")
        return False

    print("\n" + "=" * 60)
    print("✅ ALL VERIFICATION TESTS PASSED")
    print("=" * 60)
    print("\nTASK-003 is complete! You can now:")
    print("1. Start Docker Compose: docker compose up -d")
    print("2. Run migrations: alembic upgrade head")
    print("3. Proceed to TASK-004")
    print()

    return True


if __name__ == "__main__":
    success = verify_models()
    sys.exit(0 if success else 1)
