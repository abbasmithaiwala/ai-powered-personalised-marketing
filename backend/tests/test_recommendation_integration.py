"""
Integration tests for recommendation API and engine.

These tests use a real test database and verify the full flow
from API endpoint through to vector search and database queries.
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from decimal import Decimal
from unittest.mock import patch, MagicMock

from app.models.customer import Customer
from app.models.customer_preference import CustomerPreference
from app.models.brand import Brand
from app.models.menu_item import MenuItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.services.intelligence.recommendation_engine import RecommendationEngine


@pytest.mark.asyncio
class TestRecommendationAPIEndpoint:
    """Test recommendation API endpoint"""

    async def test_get_recommendations_customer_not_found(self, async_client):
        """Should return 404 when customer doesn't exist"""
        fake_customer_id = uuid4()

        response = await async_client.get(
            f"/api/v1/customers/{fake_customer_id}/recommendations"
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_get_recommendations_limit_validation(self, async_client, db_session):
        """Should validate limit parameter"""
        # Create a customer
        customer = Customer(
            email="test@example.com",
            first_name="Test",
            last_name="User",
        )
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(customer)

        # Test limit too small
        response = await async_client.get(
            f"/api/v1/customers/{customer.id}/recommendations?limit=0"
        )
        assert response.status_code == 422

        # Test limit too large
        response = await async_client.get(
            f"/api/v1/customers/{customer.id}/recommendations?limit=21"
        )
        assert response.status_code == 422

    async def test_get_recommendations_success_with_fallback(self, async_client, db_session):
        """Should return fallback recommendations when no taste profile exists"""
        # Create test data
        brand = Brand(name="Test Restaurant", cuisine_type="Italian")
        db_session.add(brand)
        await db_session.commit()
        await db_session.refresh(brand)

        # Create menu items
        menu_item = MenuItem(
            brand_id=brand.id,
            name="Margherita Pizza",
            description="Classic pizza",
            category="mains",
            cuisine_type="Italian",
            price=Decimal("12.50"),
            dietary_tags=["vegetarian"],
            is_available=True,
        )
        db_session.add(menu_item)
        await db_session.commit()
        await db_session.refresh(menu_item)

        # Create customer (no taste profile)
        customer = Customer(
            email="test@example.com",
            first_name="Test",
            last_name="User",
        )
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(customer)

        # Create an order to make item "popular"
        other_customer = Customer(
            email="other@example.com",
            first_name="Other",
            last_name="User",
        )
        db_session.add(other_customer)
        await db_session.commit()
        await db_session.refresh(other_customer)

        order = Order(
            customer_id=other_customer.id,
            brand_id=brand.id,
            order_date=datetime.now(timezone.utc),
            total_amount=Decimal("12.50"),
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=menu_item.id,
            item_name="Margherita Pizza",
            quantity=1,
            unit_price=Decimal("12.50"),
        )
        db_session.add(order_item)
        await db_session.commit()

        # Mock vector store to return no taste profile
        with patch("app.services.intelligence.recommendation_engine.vector_store") as mock_vs:
            mock_vs.get_point.return_value = None

            response = await async_client.get(
                f"/api/v1/customers/{customer.id}/recommendations?limit=5"
            )

            assert response.status_code == 200
            data = response.json()

            assert data["customer_id"] == str(customer.id)
            assert data["fallback_used"] is True
            assert "items" in data
            assert "computed_at" in data


@pytest.mark.asyncio
class TestRecommendationEngineWithDatabase:
    """Test recommendation engine with database integration"""

    async def test_exclude_recently_ordered_items(self, db_session):
        """Should exclude items ordered in the last 30 days"""
        # Create test data
        brand = Brand(name="Test Restaurant")
        db_session.add(brand)
        await db_session.commit()
        await db_session.refresh(brand)

        menu_item_1 = MenuItem(
            brand_id=brand.id,
            name="Recent Item",
            category="mains",
            is_available=True,
        )
        menu_item_2 = MenuItem(
            brand_id=brand.id,
            name="Old Item",
            category="mains",
            is_available=True,
        )
        db_session.add_all([menu_item_1, menu_item_2])
        await db_session.commit()
        await db_session.refresh(menu_item_1)
        await db_session.refresh(menu_item_2)

        customer = Customer(email="test@example.com")
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(customer)

        # Create recent order
        recent_order = Order(
            customer_id=customer.id,
            brand_id=brand.id,
            order_date=datetime.now(timezone.utc) - timedelta(days=10),
            total_amount=Decimal("10.00"),
        )
        db_session.add(recent_order)
        await db_session.commit()
        await db_session.refresh(recent_order)

        recent_order_item = OrderItem(
            order_id=recent_order.id,
            menu_item_id=menu_item_1.id,
            item_name="Recent Item",
            quantity=1,
        )
        db_session.add(recent_order_item)

        # Create old order
        old_order = Order(
            customer_id=customer.id,
            brand_id=brand.id,
            order_date=datetime.now(timezone.utc) - timedelta(days=60),
            total_amount=Decimal("10.00"),
        )
        db_session.add(old_order)
        await db_session.commit()
        await db_session.refresh(old_order)

        old_order_item = OrderItem(
            order_id=old_order.id,
            menu_item_id=menu_item_2.id,
            item_name="Old Item",
            quantity=1,
        )
        db_session.add(old_order_item)
        await db_session.commit()

        # Test exclusion
        engine = RecommendationEngine(db_session)
        recently_ordered = await engine._get_recently_ordered_items(
            customer_id=customer.id,
            days=30,
        )

        assert menu_item_1.id in recently_ordered
        assert menu_item_2.id not in recently_ordered

    async def test_fallback_recommendations_with_popular_items(self, db_session):
        """Fallback should return most popular items"""
        # Create brand and items
        brand = Brand(name="Popular Restaurant")
        db_session.add(brand)
        await db_session.commit()
        await db_session.refresh(brand)

        popular_item = MenuItem(
            brand_id=brand.id,
            name="Super Popular Dish",
            category="mains",
            price=Decimal("15.00"),
            is_available=True,
        )
        unpopular_item = MenuItem(
            brand_id=brand.id,
            name="Rarely Ordered Dish",
            category="starters",
            price=Decimal("8.00"),
            is_available=True,
        )
        db_session.add_all([popular_item, unpopular_item])
        await db_session.commit()
        await db_session.refresh(popular_item)
        await db_session.refresh(unpopular_item)

        # Create customer requesting recommendations
        customer = Customer(email="new@example.com")
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(customer)

        # Create other customers who ordered popular item
        for i in range(5):
            other_customer = Customer(email=f"other{i}@example.com")
            db_session.add(other_customer)
            await db_session.commit()
            await db_session.refresh(other_customer)

            order = Order(
                customer_id=other_customer.id,
                brand_id=brand.id,
                order_date=datetime.now(timezone.utc) - timedelta(days=i),
                total_amount=Decimal("15.00"),
            )
            db_session.add(order)
            await db_session.commit()
            await db_session.refresh(order)

            order_item = OrderItem(
                order_id=order.id,
                menu_item_id=popular_item.id,
                item_name="Super Popular Dish",
                quantity=1,
            )
            db_session.add(order_item)

        # One customer ordered unpopular item
        one_customer = Customer(email="one@example.com")
        db_session.add(one_customer)
        await db_session.commit()
        await db_session.refresh(one_customer)

        order = Order(
            customer_id=one_customer.id,
            brand_id=brand.id,
            order_date=datetime.now(timezone.utc),
            total_amount=Decimal("8.00"),
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=unpopular_item.id,
            item_name="Rarely Ordered Dish",
            quantity=1,
        )
        db_session.add(order_item)
        await db_session.commit()

        # Generate fallback recommendations
        engine = RecommendationEngine(db_session)
        recommendations = await engine._generate_fallback_recommendations(
            customer_id=customer.id,
            customer_preference=None,
            limit=5,
            exclude_recent_days=30,
        )

        # Popular item should appear first
        assert len(recommendations) >= 1
        assert recommendations[0].menu_item_id == popular_item.id
        assert "Popular choice" in recommendations[0].reason

    async def test_dietary_restrictions_respected_in_fallback(self, db_session):
        """Fallback recommendations should respect dietary restrictions"""
        # Create brand and items
        brand = Brand(name="Mixed Restaurant")
        db_session.add(brand)
        await db_session.commit()
        await db_session.refresh(brand)

        meat_item = MenuItem(
            brand_id=brand.id,
            name="Beef Burger",
            category="mains",
            dietary_tags=["meat"],
            is_available=True,
        )
        veg_item = MenuItem(
            brand_id=brand.id,
            name="Veggie Burger",
            category="mains",
            dietary_tags=["vegetarian"],
            is_available=True,
        )
        db_session.add_all([meat_item, veg_item])
        await db_session.commit()
        await db_session.refresh(meat_item)
        await db_session.refresh(veg_item)

        # Create vegetarian customer
        customer = Customer(email="veggie@example.com")
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(customer)

        preference = CustomerPreference(
            customer_id=customer.id,
            dietary_flags={"vegetarian": True},
        )
        db_session.add(preference)
        await db_session.commit()

        # Make both items popular
        for item in [meat_item, veg_item]:
            for i in range(3):
                other_customer = Customer(email=f"other_{item.name}_{i}@example.com")
                db_session.add(other_customer)
                await db_session.commit()
                await db_session.refresh(other_customer)

                order = Order(
                    customer_id=other_customer.id,
                    brand_id=brand.id,
                    order_date=datetime.now(timezone.utc),
                    total_amount=Decimal("10.00"),
                )
                db_session.add(order)
                await db_session.commit()
                await db_session.refresh(order)

                order_item = OrderItem(
                    order_id=order.id,
                    menu_item_id=item.id,
                    item_name=item.name,
                    quantity=1,
                )
                db_session.add(order_item)
        await db_session.commit()

        # Generate recommendations
        engine = RecommendationEngine(db_session)
        recommendations = await engine._generate_fallback_recommendations(
            customer_id=customer.id,
            customer_preference=preference,
            limit=5,
            exclude_recent_days=30,
        )

        # Should only get vegetarian item
        assert len(recommendations) >= 1
        for rec in recommendations:
            assert rec.menu_item_id != meat_item.id

        # Should include veggie burger
        veg_rec = next((r for r in recommendations if r.menu_item_id == veg_item.id), None)
        assert veg_rec is not None

    async def test_get_customer_brand_history(self, db_session):
        """Should correctly retrieve customer's brand history"""
        # Create brands
        brand_1 = Brand(name="Restaurant 1")
        brand_2 = Brand(name="Restaurant 2")
        brand_3 = Brand(name="Restaurant 3")
        db_session.add_all([brand_1, brand_2, brand_3])
        await db_session.commit()
        await db_session.refresh(brand_1)
        await db_session.refresh(brand_2)
        await db_session.refresh(brand_3)

        # Create customer
        customer = Customer(email="test@example.com")
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(customer)

        # Customer ordered from brand 1 and 2, but not 3
        order_1 = Order(
            customer_id=customer.id,
            brand_id=brand_1.id,
            order_date=datetime.now(timezone.utc),
            total_amount=Decimal("10.00"),
        )
        order_2 = Order(
            customer_id=customer.id,
            brand_id=brand_2.id,
            order_date=datetime.now(timezone.utc),
            total_amount=Decimal("15.00"),
        )
        db_session.add_all([order_1, order_2])
        await db_session.commit()

        # Get brand history
        engine = RecommendationEngine(db_session)
        brand_ids = await engine._get_customer_brand_ids(customer.id)

        assert brand_1.id in brand_ids
        assert brand_2.id in brand_ids
        assert brand_3.id not in brand_ids
