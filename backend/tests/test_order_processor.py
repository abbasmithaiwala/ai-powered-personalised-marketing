"""
Tests for order processing pipeline.

Tests the core order ingestion logic including:
- Brand resolution
- Customer resolution
- Menu item resolution
- Order creation
- Customer stats updates
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models.brand import Brand
from app.models.customer import Customer
from app.models.menu_item import MenuItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.schemas.csv_schemas import OrderCSVRow
from app.services.ingestion.brand_resolver import BrandResolver
from app.services.ingestion.customer_resolver import CustomerResolver
from app.services.ingestion.menu_item_resolver import MenuItemResolver
from app.services.ingestion.order_processor import OrderProcessor


@pytest.mark.asyncio
class TestBrandResolver:
    """Test brand resolution logic."""

    async def test_create_new_brand(self, db_session):
        """Test creating a new brand."""
        resolver = BrandResolver(db_session)

        csv_row = OrderCSVRow(
            order_id="ORD-001",
            customer_email="test@example.com",
            brand_name="Pizza Palace",
            item_name="Margherita Pizza",
            quantity=1,
            unit_price=Decimal("750.00"),
            order_date=datetime(2024, 1, 15, 12, 0, 0),
            row_number=1,
        )

        brand = await resolver.resolve(csv_row)
        await db_session.commit()

        assert brand is not None
        assert brand.name == "Pizza Palace"
        assert brand.is_active is True

    async def test_find_existing_brand_case_insensitive(self, db_session):
        """Test finding existing brand with case-insensitive match."""
        # Create a brand
        brand1 = Brand(name="Pizza Palace", is_active=True)
        db_session.add(brand1)
        await db_session.commit()

        resolver = BrandResolver(db_session)

        # Try to resolve with different case
        csv_row = OrderCSVRow(
            order_id="ORD-001",
            customer_email="test@example.com",
            brand_name="pizza palace",
            item_name="Margherita Pizza",
            quantity=1,
            unit_price=Decimal("750.00"),
            order_date=datetime(2024, 1, 15, 12, 0, 0),
            row_number=1,
        )

        brand = await resolver.resolve(csv_row)

        assert brand.id == brand1.id
        assert brand.name == "Pizza Palace"  # Original case preserved


@pytest.mark.asyncio
class TestCustomerResolver:
    """Test customer resolution logic."""

    async def test_create_new_customer(self, db_session):
        """Test creating a new customer."""
        resolver = CustomerResolver(db_session)

        csv_row = OrderCSVRow(
            order_id="ORD-001",
            customer_email="john@example.com",
            customer_id="CUST-001",
            customer_first_name="John",
            customer_last_name="Doe",
            customer_phone="+1234567890",
            customer_city="Ahmedabad",
            brand_name="Pizza Palace",
            item_name="Margherita Pizza",
            quantity=1,
            unit_price=Decimal("750.00"),
            order_date=datetime(2024, 1, 15, 12, 0, 0),
            row_number=1,
        )

        customer = await resolver.resolve(csv_row)
        await db_session.commit()

        assert customer is not None
        assert customer.email == "john@example.com"
        assert customer.external_id == "CUST-001"
        assert customer.first_name == "John"
        assert customer.last_name == "Doe"
        assert customer.phone == "+1234567890"
        assert customer.city == "Ahmedabad"

    async def test_find_existing_customer_by_external_id(self, db_session):
        """Test finding existing customer by external ID."""
        # Create a customer
        customer1 = Customer(
            email="john@example.com",
            external_id="CUST-001",
            first_name="John",
            last_name="Doe",
        )
        db_session.add(customer1)
        await db_session.commit()

        resolver = CustomerResolver(db_session)

        csv_row = OrderCSVRow(
            order_id="ORD-001",
            customer_email="john@example.com",
            customer_id="CUST-001",
            brand_name="Pizza Palace",
            item_name="Margherita Pizza",
            quantity=1,
            unit_price=Decimal("750.00"),
            order_date=datetime(2024, 1, 15, 12, 0, 0),
            row_number=1,
        )

        customer = await resolver.resolve(csv_row)

        assert customer.id == customer1.id

    async def test_find_existing_customer_by_email(self, db_session):
        """Test finding existing customer by email when external_id doesn't match."""
        # Create a customer
        customer1 = Customer(
            email="john@example.com",
            first_name="John",
            last_name="Doe",
        )
        db_session.add(customer1)
        await db_session.commit()

        resolver = CustomerResolver(db_session)

        csv_row = OrderCSVRow(
            order_id="ORD-001",
            customer_email="john@example.com",
            customer_id="NEW-ID",
            brand_name="Pizza Palace",
            item_name="Margherita Pizza",
            quantity=1,
            unit_price=Decimal("750.00"),
            order_date=datetime(2024, 1, 15, 12, 0, 0),
            row_number=1,
        )

        customer = await resolver.resolve(csv_row)

        assert customer.id == customer1.id


@pytest.mark.asyncio
class TestMenuItemResolver:
    """Test menu item resolution logic."""

    async def test_create_new_menu_item(self, db_session):
        """Test creating a new menu item."""
        # Create a brand first
        brand = Brand(name="Pizza Palace", is_active=True)
        db_session.add(brand)
        await db_session.commit()

        resolver = MenuItemResolver(db_session)

        csv_row = OrderCSVRow(
            order_id="ORD-001",
            customer_email="test@example.com",
            brand_name="Pizza Palace",
            item_name="Margherita Pizza",
            category="Main",
            quantity=1,
            unit_price=Decimal("750.00"),
            order_date=datetime(2024, 1, 15, 12, 0, 0),
            row_number=1,
        )

        menu_item = await resolver.resolve(csv_row, brand.id)
        await db_session.commit()

        assert menu_item is not None
        assert menu_item.name == "Margherita Pizza"
        assert menu_item.brand_id == brand.id
        assert menu_item.category == "Main"
        assert float(menu_item.price) == 750.00
        assert menu_item.is_available is True

    async def test_find_existing_menu_item(self, db_session):
        """Test finding existing menu item by name and brand."""
        # Create brand and menu item
        brand = Brand(name="Pizza Palace", is_active=True)
        db_session.add(brand)
        await db_session.commit()

        item1 = MenuItem(
            name="Margherita Pizza",
            brand_id=brand.id,
            category="Main",
            price=750.00,
        )
        db_session.add(item1)
        await db_session.commit()

        resolver = MenuItemResolver(db_session)

        csv_row = OrderCSVRow(
            order_id="ORD-001",
            customer_email="test@example.com",
            brand_name="Pizza Palace",
            item_name="margherita pizza",
            quantity=1,
            unit_price=Decimal("750.00"),
            order_date=datetime(2024, 1, 15, 12, 0, 0),
            row_number=1,
        )

        menu_item = await resolver.resolve(csv_row, brand.id)

        assert menu_item.id == item1.id


@pytest.mark.asyncio
class TestOrderProcessor:
    """Test complete order processing pipeline."""

    async def test_process_single_order(self, db_session):
        """Test processing a single order from CSV row."""
        processor = OrderProcessor(db_session)

        csv_row = OrderCSVRow(
            order_id="ORD-001",
            customer_email="john@example.com",
            customer_id="CUST-001",
            customer_first_name="John",
            customer_last_name="Doe",
            brand_name="Pizza Palace",
            item_name="Margherita Pizza",
            category="Main",
            quantity=2,
            unit_price=Decimal("500.00"),
            order_total=Decimal("1000.00"),
            order_date=datetime(2024, 1, 15, 12, 0, 0),
            row_number=1,
        )

        result = await processor.process_rows([csv_row])
        await db_session.commit()

        # Verify result
        assert result.total_rows == 1
        assert result.processed_rows == 1
        assert result.failed_rows == 0
        assert result.skipped_rows == 0
        assert len(result.affected_customer_ids) == 1

        # Verify order was created
        orders_result = await db_session.execute(
            select(Order).where(Order.external_id == "ORD-001")
        )
        order = orders_result.scalar_one()

        assert order.external_id == "ORD-001"
        assert float(order.total_amount) == 1000.00

        # Verify order items (use explicit query to avoid lazy loading)
        order_items_result = await db_session.execute(
            select(OrderItem).where(OrderItem.order_id == order.id)
        )
        order_items = order_items_result.scalars().all()
        assert len(order_items) == 1
        order_item = order_items[0]
        assert order_item.item_name == "Margherita Pizza"
        assert order_item.quantity == 2
        assert float(order_item.unit_price) == 500.00

        # Verify customer stats were updated (use explicit query)
        customer_result = await db_session.execute(
            select(Customer).where(Customer.id == order.customer_id)
        )
        customer = customer_result.scalar_one()
        assert customer.total_orders == 1
        assert float(customer.total_spend) == 1000.00
        # Verify dates are set (exact time may vary due to timezone conversion)
        assert customer.first_order_at is not None
        assert customer.last_order_at is not None
        assert customer.first_order_at.date() == datetime(2024, 1, 15).date()
        assert customer.last_order_at.date() == datetime(2024, 1, 15).date()

    async def test_process_multiple_orders_same_customer(self, db_session):
        """Test processing multiple orders for the same customer."""
        processor = OrderProcessor(db_session)

        rows = [
            OrderCSVRow(
                order_id="ORD-001",
                customer_email="john@example.com",
                customer_id="CUST-001",
                brand_name="Pizza Palace",
                item_name="Margherita Pizza",
                quantity=1,
                unit_price=Decimal("750.00"),
                order_total=Decimal("750.00"),
                order_date=datetime(2024, 1, 15, 12, 0, 0),
                row_number=1,
            ),
            OrderCSVRow(
                order_id="ORD-002",
                customer_email="john@example.com",
                customer_id="CUST-001",
                brand_name="Pizza Palace",
                item_name="Pepperoni Pizza",
                quantity=1,
                unit_price=Decimal("1000.00"),
                order_total=Decimal("1000.00"),
                order_date=datetime(2024, 1, 20, 18, 30, 0),
                row_number=2,
            ),
        ]

        result = await processor.process_rows(rows)
        await db_session.commit()

        assert result.processed_rows == 2
        assert len(result.affected_customer_ids) == 1

        # Verify customer stats
        customers_result = await db_session.execute(select(Customer))
        customers = customers_result.scalars().all()
        assert len(customers) == 1

        customer = customers[0]
        assert customer.total_orders == 2
        assert float(customer.total_spend) == 1750.00
        # Verify dates are set correctly (exact time may vary due to timezone conversion)
        assert customer.first_order_at is not None
        assert customer.last_order_at is not None
        assert customer.first_order_at.date() == datetime(2024, 1, 15).date()
        assert customer.last_order_at.date() == datetime(2024, 1, 20).date()
        # First order should be earlier than last
        assert customer.first_order_at < customer.last_order_at

    async def test_idempotency_skip_duplicate_orders(self, db_session):
        """Test that duplicate orders are skipped (idempotency)."""
        processor = OrderProcessor(db_session)

        csv_row = OrderCSVRow(
            order_id="ORD-001",
            customer_email="john@example.com",
            brand_name="Pizza Palace",
            item_name="Margherita Pizza",
            quantity=1,
            unit_price=Decimal("750.00"),
            order_total=Decimal("750.00"),
            order_date=datetime(2024, 1, 15, 12, 0, 0),
            row_number=1,
        )

        # Process first time
        result1 = await processor.process_rows([csv_row])
        await db_session.commit()

        assert result1.processed_rows == 1
        assert result1.skipped_rows == 0

        # Process second time (should skip)
        result2 = await processor.process_rows([csv_row])
        await db_session.commit()

        assert result2.processed_rows == 0
        assert result2.skipped_rows == 1

        # Verify only one order exists
        orders_result = await db_session.execute(select(Order))
        orders = orders_result.scalars().all()
        assert len(orders) == 1

    async def test_calculate_order_total_when_missing(self, db_session):
        """Test that order total is calculated from line items when not provided."""
        processor = OrderProcessor(db_session)

        csv_row = OrderCSVRow(
            order_id="ORD-001",
            customer_email="john@example.com",
            brand_name="Pizza Palace",
            item_name="Margherita Pizza",
            quantity=3,
            unit_price=Decimal("1000.00"),
            # order_total not provided
            order_date=datetime(2024, 1, 15, 12, 0, 0),
            row_number=1,
        )

        result = await processor.process_rows([csv_row])
        await db_session.commit()

        # Verify order total was calculated
        orders_result = await db_session.execute(select(Order))
        order = orders_result.scalar_one()

        assert float(order.total_amount) == 3000.00  # 3 * 1000.00

    async def test_process_multiple_brands(self, db_session):
        """Test processing orders from multiple brands."""
        processor = OrderProcessor(db_session)

        rows = [
            OrderCSVRow(
                order_id="ORD-001",
                customer_email="john@example.com",
                brand_name="Pizza Palace",
                item_name="Margherita Pizza",
                quantity=1,
                unit_price=Decimal("750.00"),
                order_date=datetime(2024, 1, 15, 12, 0, 0),
                row_number=1,
            ),
            OrderCSVRow(
                order_id="ORD-002",
                customer_email="john@example.com",
                brand_name="Burger House",
                item_name="Cheeseburger",
                quantity=1,
                unit_price=Decimal("500.00"),
                order_date=datetime(2024, 1, 16, 13, 0, 0),
                row_number=2,
            ),
        ]

        result = await processor.process_rows(rows)
        await db_session.commit()

        assert result.processed_rows == 2

        # Verify both brands were created
        brands_result = await db_session.execute(select(Brand))
        brands = brands_result.scalars().all()
        assert len(brands) == 2

        brand_names = {b.name for b in brands}
        assert brand_names == {"Pizza Palace", "Burger House"}
