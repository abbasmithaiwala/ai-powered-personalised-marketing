"""
Manual test script for Task 007 - Order Ingestion Pipeline.

This script can be run manually to verify the order processing pipeline works.

Prerequisites:
1. Docker services running (postgres, qdrant, redis)
2. Database migrated with alembic
3. .env file configured

Usage:
    python test_task007_manual.py
"""

import asyncio
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.brand import Brand
from app.models.customer import Customer
from app.models.menu_item import MenuItem
from app.models.order import Order
from app.schemas.csv_schemas import OrderCSVRow
from app.services.ingestion.order_processor import OrderProcessor


async def main():
    """Run manual tests for order processing pipeline."""
    print("=" * 80)
    print("Task 007 - Order Ingestion Pipeline - Manual Test")
    print("=" * 80)

    async with AsyncSessionLocal() as session:
        # Clean up existing test data
        print("\n1. Cleaning up existing test data...")
        await session.execute("DELETE FROM order_items WHERE TRUE")
        await session.execute("DELETE FROM orders WHERE TRUE")
        await session.execute("DELETE FROM menu_items WHERE TRUE")
        await session.execute("DELETE FROM customers WHERE TRUE")
        await session.execute("DELETE FROM brands WHERE TRUE")
        await session.commit()
        print("   ✓ Test data cleaned")

        # Test 1: Process a single order
        print("\n2. Test: Process a single order")
        processor = OrderProcessor(session)

        csv_row = OrderCSVRow(
            order_id="ORD-001",
            customer_email="john.doe@example.com",
            customer_id="CUST-001",
            customer_first_name="John",
            customer_last_name="Doe",
            customer_city="London",
            brand_name="Pizza Palace",
            item_name="Margherita Pizza",
            category="Main",
            quantity=2,
            unit_price=Decimal("12.99"),
            order_total=Decimal("25.98"),
            order_date=datetime(2024, 1, 15, 12, 0, 0),
            row_number=1,
        )

        result = await processor.process_rows([csv_row])
        await session.commit()

        print(f"   Total rows: {result.total_rows}")
        print(f"   Processed: {result.processed_rows}")
        print(f"   Failed: {result.failed_rows}")
        print(f"   Skipped: {result.skipped_rows}")
        print(f"   Affected customers: {len(result.affected_customer_ids)}")

        assert result.processed_rows == 1, "Should process 1 row"
        assert result.failed_rows == 0, "Should have no failures"
        print("   ✓ Single order processed successfully")

        # Verify data was created
        print("\n3. Verifying data was created...")

        # Check brand
        brands_result = await session.execute(select(Brand))
        brands = brands_result.scalars().all()
        assert len(brands) == 1, "Should have 1 brand"
        assert brands[0].name == "Pizza Palace"
        print(f"   ✓ Brand created: {brands[0].name}")

        # Check customer
        customers_result = await session.execute(select(Customer))
        customers = customers_result.scalars().all()
        assert len(customers) == 1, "Should have 1 customer"
        customer = customers[0]
        assert customer.email == "john.doe@example.com"
        assert customer.external_id == "CUST-001"
        assert customer.first_name == "John"
        assert customer.last_name == "Doe"
        assert customer.total_orders == 1
        assert float(customer.total_spend) == 25.98
        print(f"   ✓ Customer created: {customer.email}")
        print(f"     - Total orders: {customer.total_orders}")
        print(f"     - Total spend: ${customer.total_spend}")

        # Check menu item
        items_result = await session.execute(select(MenuItem))
        items = items_result.scalars().all()
        assert len(items) == 1, "Should have 1 menu item"
        assert items[0].name == "Margherita Pizza"
        assert items[0].category == "Main"
        print(f"   ✓ Menu item created: {items[0].name}")

        # Check order
        orders_result = await session.execute(select(Order))
        orders = orders_result.scalars().all()
        assert len(orders) == 1, "Should have 1 order"
        order = orders[0]
        assert order.external_id == "ORD-001"
        assert float(order.total_amount) == 25.98
        assert len(order.order_items) == 1
        print(f"   ✓ Order created: {order.external_id}")
        print(f"     - Total amount: ${order.total_amount}")
        print(f"     - Order items: {len(order.order_items)}")

        # Test 2: Process multiple orders for same customer
        print("\n4. Test: Process multiple orders for same customer")

        rows = [
            OrderCSVRow(
                order_id="ORD-002",
                customer_email="john.doe@example.com",
                customer_id="CUST-001",
                brand_name="Pizza Palace",
                item_name="Pepperoni Pizza",
                quantity=1,
                unit_price=Decimal("14.99"),
                order_total=Decimal("14.99"),
                order_date=datetime(2024, 1, 20, 18, 30, 0),
                row_number=2,
            ),
            OrderCSVRow(
                order_id="ORD-003",
                customer_email="john.doe@example.com",
                customer_id="CUST-001",
                brand_name="Burger House",
                item_name="Cheeseburger",
                quantity=1,
                unit_price=Decimal("8.99"),
                order_total=Decimal("8.99"),
                order_date=datetime(2024, 1, 25, 19, 0, 0),
                row_number=3,
            ),
        ]

        result = await processor.process_rows(rows)
        await session.commit()

        print(f"   Processed: {result.processed_rows}")
        assert result.processed_rows == 2, "Should process 2 rows"
        print("   ✓ Multiple orders processed")

        # Verify customer stats updated
        await session.refresh(customer)
        assert customer.total_orders == 3, "Should have 3 total orders"
        assert float(customer.total_spend) == 49.96, "Should have correct total spend"
        print(f"   ✓ Customer stats updated:")
        print(f"     - Total orders: {customer.total_orders}")
        print(f"     - Total spend: ${customer.total_spend}")

        # Test 3: Idempotency (duplicate order should be skipped)
        print("\n5. Test: Idempotency - duplicate order should be skipped")

        duplicate_row = OrderCSVRow(
            order_id="ORD-001",  # Same as first order
            customer_email="john.doe@example.com",
            brand_name="Pizza Palace",
            item_name="Margherita Pizza",
            quantity=2,
            unit_price=Decimal("12.99"),
            order_date=datetime(2024, 1, 15, 12, 0, 0),
            row_number=4,
        )

        result = await processor.process_rows([duplicate_row])
        await session.commit()

        print(f"   Processed: {result.processed_rows}")
        print(f"   Skipped: {result.skipped_rows}")
        assert result.processed_rows == 0, "Should process 0 rows"
        assert result.skipped_rows == 1, "Should skip 1 row"
        print("   ✓ Duplicate order skipped (idempotency working)")

        # Verify still only 3 orders
        orders_result = await session.execute(select(Order))
        orders = orders_result.scalars().all()
        assert len(orders) == 3, "Should still have 3 orders"
        print(f"   ✓ Total orders unchanged: {len(orders)}")

        # Test 4: Case-insensitive matching
        print("\n6. Test: Case-insensitive brand matching")

        case_test_row = OrderCSVRow(
            order_id="ORD-004",
            customer_email="jane@example.com",
            brand_name="pizza palace",  # Different case
            item_name="Hawaiian Pizza",
            quantity=1,
            unit_price=Decimal("13.99"),
            order_date=datetime(2024, 1, 26, 12, 0, 0),
            row_number=5,
        )

        result = await processor.process_rows([case_test_row])
        await session.commit()

        # Should still only have 2 brands (Pizza Palace and Burger House)
        brands_result = await session.execute(select(Brand))
        brands = brands_result.scalars().all()
        assert len(brands) == 2, "Should still have 2 brands (case-insensitive match)"
        print(f"   ✓ Case-insensitive matching working: {len(brands)} brands total")

        print("\n" + "=" * 80)
        print("All tests passed! ✓")
        print("=" * 80)

        # Print summary
        print("\nFinal Database State:")
        print(f"  Brands: {len(brands)}")
        customers_result = await session.execute(select(Customer))
        customers = customers_result.scalars().all()
        print(f"  Customers: {len(customers)}")
        items_result = await session.execute(select(MenuItem))
        items = items_result.scalars().all()
        print(f"  Menu Items: {len(items)}")
        orders_result = await session.execute(select(Order))
        orders = orders_result.scalars().all()
        print(f"  Orders: {len(orders)}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
