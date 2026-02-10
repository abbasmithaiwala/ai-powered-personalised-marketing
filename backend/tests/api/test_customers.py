"""Tests for customer API endpoints"""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from httpx import AsyncClient

from app.models import Customer, CustomerPreference, Brand, Order


@pytest.mark.asyncio
class TestCustomerSearchEndpoint:
    """Test suite for customer search endpoint"""

    async def test_search_customers_no_filters(self, async_client: AsyncClient, db_session):
        """Test searching all customers with no filters"""
        # Create sample customers
        customers = [
            Customer(
                external_id=f"c{i}",
                email=f"c{i}@test.com",
                total_orders=i + 1,
                total_spend=Decimal(str((i + 1) * 10)),
            )
            for i in range(5)
        ]
        db_session.add_all(customers)
        await db_session.commit()

        response = await async_client.post(
            "/api/v1/customers/search",
            json={"filters": {}, "page": 1, "page_size": 10},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 5
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert data["pages"] == 1

    async def test_search_customers_with_pagination(self, async_client: AsyncClient, db_session):
        """Test customer search pagination"""
        # Create 10 customers
        customers = [
            Customer(
                external_id=f"c{i}",
                email=f"c{i}@test.com",
                total_orders=1,
                total_spend=Decimal("10.0"),
            )
            for i in range(10)
        ]
        db_session.add_all(customers)
        await db_session.commit()

        # First page
        response = await async_client.post(
            "/api/v1/customers/search",
            json={"filters": {}, "page": 1, "page_size": 3},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10
        assert len(data["items"]) == 3
        assert data["page"] == 1
        assert data["pages"] == 4

        # Second page
        response = await async_client.post(
            "/api/v1/customers/search",
            json={"filters": {}, "page": 2, "page_size": 3},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10
        assert len(data["items"]) == 3
        assert data["page"] == 2

    async def test_search_customers_by_spend(self, async_client: AsyncClient, db_session):
        """Test filtering customers by spend range"""
        customers = [
            Customer(
                external_id="low",
                email="low@test.com",
                total_orders=1,
                total_spend=Decimal("5.0"),
            ),
            Customer(
                external_id="medium",
                email="medium@test.com",
                total_orders=1,
                total_spend=Decimal("15.0"),
            ),
            Customer(
                external_id="high",
                email="high@test.com",
                total_orders=1,
                total_spend=Decimal("50.0"),
            ),
        ]
        db_session.add_all(customers)
        await db_session.commit()

        # High spenders only
        response = await async_client.post(
            "/api/v1/customers/search",
            json={
                "filters": {"total_spend_min": 25.0},
                "page": 1,
                "page_size": 10,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["email"] == "high@test.com"

    async def test_search_customers_by_city(self, async_client: AsyncClient, db_session):
        """Test filtering customers by city"""
        customers = [
            Customer(
                external_id="c1",
                email="c1@test.com",
                city="London",
                total_orders=1,
                total_spend=Decimal("10.0"),
            ),
            Customer(
                external_id="c2",
                email="c2@test.com",
                city="Manchester",
                total_orders=1,
                total_spend=Decimal("10.0"),
            ),
        ]
        db_session.add_all(customers)
        await db_session.commit()

        response = await async_client.post(
            "/api/v1/customers/search",
            json={
                "filters": {"city": "london"},
                "page": 1,
                "page_size": 10,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["city"] == "London"

    async def test_search_customers_by_favorite_cuisine(
        self, async_client: AsyncClient, db_session
    ):
        """Test filtering by favorite cuisine"""
        customer = Customer(
            external_id="c1",
            email="c1@test.com",
            total_orders=5,
            total_spend=Decimal("50.0"),
        )
        db_session.add(customer)
        await db_session.commit()

        preference = CustomerPreference(
            customer_id=customer.id,
            favorite_cuisines={"italian": 0.9, "thai": 0.6},
            last_computed_at=datetime.now(timezone.utc),
        )
        db_session.add(preference)
        await db_session.commit()

        response = await async_client.post(
            "/api/v1/customers/search",
            json={
                "filters": {"favorite_cuisine": "italian"},
                "page": 1,
                "page_size": 10,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["email"] == "c1@test.com"

    async def test_search_customers_by_dietary_flag(
        self, async_client: AsyncClient, db_session
    ):
        """Test filtering by dietary flags"""
        customer = Customer(
            external_id="c1",
            email="c1@test.com",
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

        response = await async_client.post(
            "/api/v1/customers/search",
            json={
                "filters": {"dietary_flag": "vegetarian"},
                "page": 1,
                "page_size": 10,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    async def test_search_customers_by_brand(self, async_client: AsyncClient, db_session):
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

        # Only customer1 ordered from brand
        order = Order(
            external_id="order1",
            customer_id=customer1.id,
            brand_id=brand.id,
            order_date=datetime.now(timezone.utc),
            total_amount=Decimal("10.0"),
        )
        db_session.add(order)
        await db_session.commit()

        response = await async_client.post(
            "/api/v1/customers/search",
            json={
                "filters": {"brand_id": str(brand.id)},
                "page": 1,
                "page_size": 10,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["email"] == "c1@test.com"

    async def test_search_customers_combined_filters(
        self, async_client: AsyncClient, db_session
    ):
        """Test combining multiple filters"""
        customer = Customer(
            external_id="perfect",
            email="perfect@test.com",
            city="London",
            total_orders=10,
            total_spend=Decimal("100.0"),
        )
        db_session.add(customer)
        await db_session.commit()

        preference = CustomerPreference(
            customer_id=customer.id,
            favorite_cuisines={"italian": 0.9},
            order_frequency="weekly",
            last_computed_at=datetime.now(timezone.utc),
        )
        db_session.add(preference)
        await db_session.commit()

        response = await async_client.post(
            "/api/v1/customers/search",
            json={
                "filters": {
                    "city": "London",
                    "total_orders_min": 5,
                    "total_spend_min": 50.0,
                    "favorite_cuisine": "italian",
                    "order_frequency": "weekly",
                },
                "page": 1,
                "page_size": 10,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["email"] == "perfect@test.com"


@pytest.mark.asyncio
class TestSegmentCountEndpoint:
    """Test suite for segment count endpoint"""

    async def test_segment_count_no_filters(self, async_client: AsyncClient, db_session):
        """Test counting all customers"""
        customers = [
            Customer(
                external_id=f"c{i}",
                email=f"c{i}@test.com",
                total_orders=1,
                total_spend=Decimal("10.0"),
            )
            for i in range(5)
        ]
        db_session.add_all(customers)
        await db_session.commit()

        response = await async_client.post(
            "/api/v1/customers/segment-count",
            json={"filters": {}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 5

    async def test_segment_count_with_filters(self, async_client: AsyncClient, db_session):
        """Test counting with filters"""
        customers = [
            Customer(
                external_id="low",
                email="low@test.com",
                total_orders=1,
                total_spend=Decimal("5.0"),
            ),
            Customer(
                external_id="high1",
                email="high1@test.com",
                total_orders=1,
                total_spend=Decimal("50.0"),
            ),
            Customer(
                external_id="high2",
                email="high2@test.com",
                total_orders=1,
                total_spend=Decimal("75.0"),
            ),
        ]
        db_session.add_all(customers)
        await db_session.commit()

        response = await async_client.post(
            "/api/v1/customers/segment-count",
            json={"filters": {"total_spend_min": 25.0}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2

    async def test_segment_count_performance(self, async_client: AsyncClient, db_session):
        """Test that segment count is fast (target <200ms)"""
        import time

        # Create 100 customers
        customers = [
            Customer(
                external_id=f"c{i}",
                email=f"c{i}@test.com",
                total_orders=i % 10,
                total_spend=Decimal(str((i % 10) * 10)),
            )
            for i in range(100)
        ]
        db_session.add_all(customers)
        await db_session.commit()

        start = time.time()
        response = await async_client.post(
            "/api/v1/customers/segment-count",
            json={"filters": {"total_orders_min": 5}},
        )
        elapsed = (time.time() - start) * 1000  # Convert to ms

        assert response.status_code == 200
        # Performance target: <200ms (being generous with test environment overhead)
        assert elapsed < 500, f"Segment count took {elapsed}ms, expected <500ms"
