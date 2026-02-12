"""Tests for customer segmentation service"""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from app.services.segmentation_service import SegmentationService
from app.schemas.campaign import SegmentFilters
from app.models import Customer, CustomerPreference, Brand, Order


@pytest.mark.asyncio
class TestSegmentationService:
    """Test suite for SegmentationService"""

    async def test_count_segment_empty_filters(self, db_session, sample_customers):
        """Test counting all customers with no filters"""
        service = SegmentationService(db_session)
        count = await service.count_segment(SegmentFilters())
        assert count == len(sample_customers)

    async def test_count_segment_by_spend(self, db_session, sample_customers):
        """Test filtering customers by spend range"""
        service = SegmentationService(db_session)

        # High spenders (>£25)
        filters = SegmentFilters(total_spend_min=25.0)
        count = await service.count_segment(filters)
        expected = sum(1 for c in sample_customers if c.total_spend >= 25)
        assert count == expected

        # Medium spenders (£10-25)
        filters = SegmentFilters(total_spend_min=10.0, total_spend_max=25.0)
        count = await service.count_segment(filters)
        expected = sum(1 for c in sample_customers if 10 <= c.total_spend <= 25)
        assert count == expected

    async def test_count_segment_by_orders(self, db_session, sample_customers):
        """Test filtering customers by order count"""
        service = SegmentationService(db_session)

        filters = SegmentFilters(total_orders_min=3)
        count = await service.count_segment(filters)
        expected = sum(1 for c in sample_customers if c.total_orders >= 3)
        assert count == expected

    async def test_count_segment_by_city(self, db_session, sample_customers):
        """Test filtering customers by city"""
        service = SegmentationService(db_session)

        # Exact match (case-insensitive)
        filters = SegmentFilters(city="london")
        count = await service.count_segment(filters)
        expected = sum(
            1 for c in sample_customers if c.city and "london" in c.city.lower()
        )
        assert count == expected

    async def test_count_segment_by_multiple_cities(self, db_session, sample_customers):
        """Test filtering customers by multiple cities separated by commas"""
        service = SegmentationService(db_session)

        # Multiple cities - should match London and Manchester customers
        filters = SegmentFilters(city="London, Manchester")
        count = await service.count_segment(filters)
        expected = sum(
            1
            for c in sample_customers
            if c.city and ("london" in c.city.lower() or "manchester" in c.city.lower())
        )
        assert count == expected

        # Should return 0 if no cities match
        filters = SegmentFilters(city="Paris, Berlin")
        count = await service.count_segment(filters)
        assert count == 0

    async def test_count_segment_by_last_order_date(self, db_session):
        """Test filtering customers by last order date"""
        # Create customers with different last order dates
        now = datetime.now(timezone.utc)
        recent = Customer(
            external_id="recent",
            email="recent@test.com",
            total_orders=1,
            total_spend=Decimal("10.0"),
            last_order_at=now - timedelta(days=5),
        )
        old = Customer(
            external_id="old",
            email="old@test.com",
            total_orders=1,
            total_spend=Decimal("10.0"),
            last_order_at=now - timedelta(days=60),
        )
        db_session.add_all([recent, old])
        await db_session.commit()

        service = SegmentationService(db_session)

        # Recent customers (last 30 days)
        cutoff = now - timedelta(days=30)
        filters = SegmentFilters(last_order_after=cutoff)
        count = await service.count_segment(filters)
        assert count >= 1  # At least the recent customer

    async def test_find_customers_with_pagination(self, db_session, sample_customers):
        """Test finding customers with pagination"""
        service = SegmentationService(db_session)

        # First page
        customers, total = await service.find_customers(
            SegmentFilters(), limit=2, offset=0
        )
        assert len(customers) <= 2
        assert total == len(sample_customers)

        # Second page
        customers, total = await service.find_customers(
            SegmentFilters(), limit=2, offset=2
        )
        assert len(customers) <= 2
        assert total == len(sample_customers)

    async def test_find_customers_ordered_by_recency(self, db_session):
        """Test that customers are ordered by most recent order first"""
        now = datetime.now(timezone.utc)
        customer1 = Customer(
            external_id="c1",
            email="c1@test.com",
            total_orders=1,
            total_spend=Decimal("10.0"),
            last_order_at=now - timedelta(days=10),
        )
        customer2 = Customer(
            external_id="c2",
            email="c2@test.com",
            total_orders=1,
            total_spend=Decimal("10.0"),
            last_order_at=now - timedelta(days=5),
        )
        customer3 = Customer(
            external_id="c3",
            email="c3@test.com",
            total_orders=1,
            total_spend=Decimal("10.0"),
            last_order_at=now - timedelta(days=15),
        )
        db_session.add_all([customer1, customer2, customer3])
        await db_session.commit()

        service = SegmentationService(db_session)
        customers, _ = await service.find_customers(SegmentFilters(), limit=10)

        # Should be ordered by last_order_at descending
        assert customers[0].last_order_at > customers[1].last_order_at

    async def test_filter_by_favorite_cuisine(self, db_session):
        """Test filtering by favorite cuisine from preferences"""
        customer = Customer(
            external_id="cust1",
            email="cust1@test.com",
            total_orders=5,
            total_spend=Decimal("50.0"),
        )
        db_session.add(customer)
        await db_session.commit()

        preference = CustomerPreference(
            customer_id=customer.id,
            favorite_cuisines={"italian": 0.8, "thai": 0.6},
            last_computed_at=datetime.now(timezone.utc),
        )
        db_session.add(preference)
        await db_session.commit()

        service = SegmentationService(db_session)

        # Should find customer who likes Italian
        filters = SegmentFilters(favorite_cuisine="italian")
        count = await service.count_segment(filters)
        assert count >= 1

        # Should not find customer for cuisine they don't like
        filters = SegmentFilters(favorite_cuisine="mexican")
        count = await service.count_segment(filters)
        assert count == 0

    async def test_filter_by_favorite_cuisine_case_insensitive(self, db_session):
        """Test filtering by favorite cuisine is case-insensitive"""
        customer = Customer(
            external_id="cust1",
            email="cust1@test.com",
            total_orders=5,
            total_spend=Decimal("50.0"),
        )
        db_session.add(customer)
        await db_session.commit()

        preference = CustomerPreference(
            customer_id=customer.id,
            favorite_cuisines={"italian": 0.8, "thai": 0.6},
            last_computed_at=datetime.now(timezone.utc),
        )
        db_session.add(preference)
        await db_session.commit()

        service = SegmentationService(db_session)

        # Should find customer regardless of case - uppercase
        filters = SegmentFilters(favorite_cuisine="ITALIAN")
        count = await service.count_segment(filters)
        assert count >= 1

        # Should find customer regardless of case - mixed case
        filters = SegmentFilters(favorite_cuisine="Italian")
        count = await service.count_segment(filters)
        assert count >= 1

        # Should find customer regardless of case - title case
        filters = SegmentFilters(favorite_cuisine="Thai")
        count = await service.count_segment(filters)
        assert count >= 1

    async def test_filter_by_dietary_flag(self, db_session):
        """Test filtering by dietary flags from preferences"""
        customer = Customer(
            external_id="cust1",
            email="cust1@test.com",
            total_orders=5,
            total_spend=Decimal("50.0"),
        )
        db_session.add(customer)
        await db_session.commit()

        preference = CustomerPreference(
            customer_id=customer.id,
            dietary_flags={"vegetarian": True, "vegan": False},
            last_computed_at=datetime.now(timezone.utc),
        )
        db_session.add(preference)
        await db_session.commit()

        service = SegmentationService(db_session)

        # Should find vegetarian customer
        filters = SegmentFilters(dietary_flag="vegetarian")
        count = await service.count_segment(filters)
        assert count >= 1

        # Should not find vegan customer
        filters = SegmentFilters(dietary_flag="vegan")
        count = await service.count_segment(filters)
        assert count == 0

    async def test_filter_by_order_frequency(self, db_session):
        """Test filtering by order frequency from preferences"""
        customer = Customer(
            external_id="cust1",
            email="cust1@test.com",
            total_orders=15,
            total_spend=Decimal("150.0"),
        )
        db_session.add(customer)
        await db_session.commit()

        preference = CustomerPreference(
            customer_id=customer.id,
            order_frequency="weekly",
            last_computed_at=datetime.now(timezone.utc),
        )
        db_session.add(preference)
        await db_session.commit()

        service = SegmentationService(db_session)

        # Should find weekly orderer
        filters = SegmentFilters(order_frequency="weekly")
        count = await service.count_segment(filters)
        assert count >= 1

        # Should not find daily orderer
        filters = SegmentFilters(order_frequency="daily")
        count = await service.count_segment(filters)
        assert count == 0

    async def test_filter_by_brand(self, db_session):
        """Test filtering customers who ordered from specific brand"""
        brand = Brand(name="Test Restaurant", slug="test-restaurant")
        db_session.add(brand)
        await db_session.commit()

        customer1 = Customer(
            external_id="c1",
            email="c1@test.com",
            total_orders=1,
            total_spend=Decimal("10.0"),
        )
        customer2 = Customer(
            external_id="c2",
            email="c2@test.com",
            total_orders=1,
            total_spend=Decimal("10.0"),
        )
        db_session.add_all([customer1, customer2])
        await db_session.commit()

        # Customer 1 ordered from brand
        order = Order(
            external_id="order1",
            customer_id=customer1.id,
            brand_id=brand.id,
            order_date=datetime.now(timezone.utc),
            total_amount=Decimal("10.0"),
        )
        db_session.add(order)
        await db_session.commit()

        service = SegmentationService(db_session)

        # Should only find customer1
        filters = SegmentFilters(brand_id=brand.id)
        customers, count = await service.find_customers(filters, limit=10)
        assert count == 1
        assert customers[0].id == customer1.id

    async def test_combined_filters(self, db_session):
        """Test combining multiple filters with AND logic"""
        customer = Customer(
            external_id="perfect_match",
            email="perfect@test.com",
            city="London",
            total_orders=10,
            total_spend=Decimal("100.0"),
            last_order_at=datetime.now(timezone.utc) - timedelta(days=5),
        )
        db_session.add(customer)
        await db_session.commit()

        preference = CustomerPreference(
            customer_id=customer.id,
            favorite_cuisines={"italian": 0.9},
            dietary_flags={"vegetarian": True},
            order_frequency="weekly",
            last_computed_at=datetime.now(timezone.utc),
        )
        db_session.add(preference)
        await db_session.commit()

        service = SegmentationService(db_session)

        # All filters should match
        filters = SegmentFilters(
            city="London",
            total_orders_min=5,
            total_spend_min=50.0,
            favorite_cuisine="italian",
            dietary_flag="vegetarian",
            order_frequency="weekly",
        )
        count = await service.count_segment(filters)
        assert count >= 1


@pytest.fixture
async def sample_customers(db_session):
    """Create sample customers for testing"""
    customers = [
        Customer(
            external_id="c1",
            email="c1@test.com",
            city="London",
            total_orders=5,
            total_spend=Decimal("50.0"),
            last_order_at=datetime.now(timezone.utc) - timedelta(days=10),
        ),
        Customer(
            external_id="c2",
            email="c2@test.com",
            city="Manchester",
            total_orders=2,
            total_spend=Decimal("15.0"),
            last_order_at=datetime.now(timezone.utc) - timedelta(days=20),
        ),
        Customer(
            external_id="c3",
            email="c3@test.com",
            city="London",
            total_orders=10,
            total_spend=Decimal("100.0"),
            last_order_at=datetime.now(timezone.utc) - timedelta(days=5),
        ),
    ]
    db_session.add_all(customers)
    await db_session.commit()
    return customers
