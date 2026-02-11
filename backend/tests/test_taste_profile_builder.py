"""
Unit tests for taste profile builder.
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
import math

from app.services.intelligence.taste_profile_builder import TasteProfileBuilder
from app.models.customer import Customer
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.menu_item import MenuItem
from app.models.brand import Brand
from app.core.constants import VECTOR_DIMENSION


class TestRecencyWeightComputation:
    """Tests for recency weight calculation"""

    def test_same_day_order(self):
        """Order from today should have weight close to 1.0"""
        now = datetime.now(timezone.utc)
        weight = TasteProfileBuilder.compute_recency_weight(now)
        assert weight == pytest.approx(1.0, abs=0.01)

    def test_recent_order_30_days(self):
        """Order from 30 days ago should have weight ~0.7"""
        now = datetime.now(timezone.utc)
        order_date = now - timedelta(days=30)
        weight = TasteProfileBuilder.compute_recency_weight(order_date)

        # exp(-30/90) ≈ 0.717
        assert weight == pytest.approx(0.717, abs=0.05)

    def test_medium_age_order_90_days(self):
        """Order from 90 days ago should have weight ~0.37"""
        now = datetime.now(timezone.utc)
        order_date = now - timedelta(days=90)
        weight = TasteProfileBuilder.compute_recency_weight(order_date)

        # exp(-90/90) = exp(-1) ≈ 0.368
        assert weight == pytest.approx(0.368, abs=0.05)

    def test_old_order_180_days(self):
        """Order from 180 days ago should have weight ~0.14"""
        now = datetime.now(timezone.utc)
        order_date = now - timedelta(days=180)
        weight = TasteProfileBuilder.compute_recency_weight(order_date)

        # exp(-180/90) = exp(-2) ≈ 0.135
        assert weight == pytest.approx(0.135, abs=0.05)

    def test_very_old_order_365_days(self):
        """Order from 365 days ago should have very low weight"""
        now = datetime.now(timezone.utc)
        order_date = now - timedelta(days=365)
        weight = TasteProfileBuilder.compute_recency_weight(order_date)

        # exp(-365/90) ≈ 0.015
        assert weight < 0.05
        assert weight > 0.0

    def test_naive_datetime_handling(self):
        """Should handle naive datetimes by adding UTC timezone"""
        # Create naive datetime (no timezone)
        naive_now = datetime.now()
        weight = TasteProfileBuilder.compute_recency_weight(naive_now)

        # Should not raise error and should return weight close to 1.0
        assert weight == pytest.approx(1.0, abs=0.01)


class TestL2Normalization:
    """Tests for L2 vector normalization"""

    def test_normalize_unit_vector(self):
        """L2 normalizing a unit vector should return same vector"""
        vector = [1.0, 0.0, 0.0]
        normalized = TasteProfileBuilder._l2_normalize(vector)

        assert normalized == pytest.approx([1.0, 0.0, 0.0])

    def test_normalize_arbitrary_vector(self):
        """L2 normalization should make magnitude = 1"""
        vector = [3.0, 4.0, 0.0]  # Magnitude = 5
        normalized = TasteProfileBuilder._l2_normalize(vector)

        # Should be [0.6, 0.8, 0.0]
        assert normalized[0] == pytest.approx(0.6)
        assert normalized[1] == pytest.approx(0.8)
        assert normalized[2] == pytest.approx(0.0)

        # Verify magnitude = 1
        magnitude = math.sqrt(sum(x * x for x in normalized))
        assert magnitude == pytest.approx(1.0)

    def test_normalize_zero_vector(self):
        """Zero vector should remain zero (avoid division by zero)"""
        vector = [0.0, 0.0, 0.0]
        normalized = TasteProfileBuilder._l2_normalize(vector)

        assert normalized == [0.0, 0.0, 0.0]

    def test_normalize_high_dimensional(self):
        """Should work with VECTOR_DIMENSION dimensions"""
        vector = [1.0] * VECTOR_DIMENSION
        normalized = TasteProfileBuilder._l2_normalize(vector)

        # Magnitude should be 1
        magnitude = math.sqrt(sum(x * x for x in normalized))
        assert magnitude == pytest.approx(1.0)

        # All components should be equal
        expected_value = 1.0 / math.sqrt(VECTOR_DIMENSION)
        for val in normalized:
            assert val == pytest.approx(expected_value, abs=0.0001)


@pytest.mark.asyncio
class TestTasteProfileBuilder:
    """Integration tests for taste profile building"""

    async def test_customer_not_found(self, db_session):
        """Should return None if customer doesn't exist"""
        builder = TasteProfileBuilder(db_session)
        fake_id = uuid4()

        result = await builder.build_taste_profile(fake_id)

        assert result is None

    async def test_customer_no_orders(self, db_session):
        """Should return insufficient_data status if customer has no orders"""
        # Create customer with no orders
        customer = Customer(
            external_id="test-001",
            email="test@example.com",
            first_name="Test",
            last_name="User",
        )
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(customer)

        builder = TasteProfileBuilder(db_session)

        with patch(
            "app.services.intelligence.taste_profile_builder.vector_store"
        ) as mock_vs:
            mock_vs.is_connected = True

            result = await builder.build_taste_profile(customer.id)

        assert result is not None
        assert result["status"] == "insufficient_data"
        assert result["reason"] == "no_orders"

    async def test_customer_no_embedded_items(self, db_session):
        """Should return insufficient_data if no items have embeddings"""
        # Create brand
        brand = Brand(name="Test Brand", slug="test-brand", cuisine_type="Italian")
        db_session.add(brand)
        await db_session.commit()
        await db_session.refresh(brand)

        # Create customer
        customer = Customer(
            external_id="test-002",
            email="test2@example.com",
            first_name="Jane",
            last_name="Doe",
        )
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(customer)

        # Create menu item WITHOUT embedding_id
        menu_item = MenuItem(
            brand_id=brand.id,
            name="Pasta",
            category="Main",
            cuisine_type="Italian",
            price=12.50,
            is_available=True,
            # Note: no embedding_id set
        )
        db_session.add(menu_item)
        await db_session.commit()
        await db_session.refresh(menu_item)

        # Create order with order item
        order = Order(
            external_id="order-001",
            customer_id=customer.id,
            brand_id=brand.id,
            order_date=datetime.now(timezone.utc),
            total_amount=12.50,
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=menu_item.id,
            item_name="Pasta",
            quantity=1,
            unit_price=12.50,
            subtotal=12.50,
        )
        db_session.add(order_item)
        await db_session.commit()

        builder = TasteProfileBuilder(db_session)

        with patch(
            "app.services.intelligence.taste_profile_builder.vector_store"
        ) as mock_vs:
            mock_vs.is_connected = True

            result = await builder.build_taste_profile(customer.id)

        assert result is not None
        assert result["status"] == "insufficient_data"
        assert result["reason"] == "no_embedded_items"
        assert result["items_skipped"] == 1

    async def test_successful_profile_build(self, db_session):
        """Should successfully build taste profile from order history"""
        # Create brand
        brand = Brand(
            name="Italian Restaurant", slug="italian-rest", cuisine_type="Italian"
        )
        db_session.add(brand)
        await db_session.commit()
        await db_session.refresh(brand)

        # Create customer
        customer = Customer(
            external_id="test-003",
            email="test3@example.com",
            first_name="John",
            last_name="Smith",
        )
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(customer)

        # Create menu items with embeddings
        item1 = MenuItem(
            brand_id=brand.id,
            name="Margherita Pizza",
            category="Main",
            cuisine_type="Italian",
            price=15.00,
            is_available=True,
            embedding_id=str(uuid4()),  # Has embedding
        )
        item2 = MenuItem(
            brand_id=brand.id,
            name="Tiramisu",
            category="Dessert",
            cuisine_type="Italian",
            price=8.00,
            is_available=True,
            embedding_id=str(uuid4()),  # Has embedding
        )
        db_session.add_all([item1, item2])
        await db_session.commit()
        await db_session.refresh(item1)
        await db_session.refresh(item2)

        # Create orders
        now = datetime.now(timezone.utc)
        order1 = Order(
            external_id="order-101",
            customer_id=customer.id,
            brand_id=brand.id,
            order_date=now - timedelta(days=10),
            total_amount=15.00,
        )
        order2 = Order(
            external_id="order-102",
            customer_id=customer.id,
            brand_id=brand.id,
            order_date=now - timedelta(days=30),
            total_amount=8.00,
        )
        db_session.add_all([order1, order2])
        await db_session.commit()
        await db_session.refresh(order1)
        await db_session.refresh(order2)

        # Create order items
        order_item1 = OrderItem(
            order_id=order1.id,
            menu_item_id=item1.id,
            item_name="Margherita Pizza",
            quantity=2,  # Quantity matters
            unit_price=15.00,
            subtotal=30.00,
        )
        order_item2 = OrderItem(
            order_id=order2.id,
            menu_item_id=item2.id,
            item_name="Tiramisu",
            quantity=1,
            unit_price=8.00,
            subtotal=8.00,
        )
        db_session.add_all([order_item1, order_item2])
        await db_session.commit()

        # Mock vector store
        builder = TasteProfileBuilder(db_session)

        # Create fake embeddings
        embedding1 = [0.5] * VECTOR_DIMENSION
        embedding2 = [-0.3] * VECTOR_DIMENSION

        mock_point1 = MagicMock()
        mock_point1.vector = embedding1

        mock_point2 = MagicMock()
        mock_point2.vector = embedding2

        with patch(
            "app.services.intelligence.taste_profile_builder.vector_store"
        ) as mock_vs:
            mock_vs.is_connected = True

            # Mock get_point to return embeddings
            # Note: Now using embedding_id instead of item.id
            async def mock_get_point(collection_name, point_id):
                if point_id == item1.embedding_id:
                    return mock_point1
                elif point_id == item2.embedding_id:
                    return mock_point2
                return None

            mock_vs.get_point = AsyncMock(side_effect=mock_get_point)
            mock_vs.upsert_points = AsyncMock(return_value=True)

            result = await builder.build_taste_profile(customer.id)

        assert result is not None
        assert result["status"] == "success"
        assert result["items_processed"] == 2
        assert result["items_skipped"] == 0
        assert result["total_weight"] > 0

        # Verify upsert was called with normalized vector
        assert mock_vs.upsert_points.called
        call_args = mock_vs.upsert_points.call_args
        points = call_args[1]["points"]
        assert len(points) == 1

        # Verify vector is normalized (magnitude = 1)
        profile_vector = points[0].vector
        magnitude = math.sqrt(sum(x * x for x in profile_vector))
        assert magnitude == pytest.approx(1.0, abs=0.01)

    async def test_vector_store_not_connected(self, db_session):
        """Should return None if vector store is not connected"""
        customer = Customer(
            external_id="test-004",
            email="test4@example.com",
        )
        db_session.add(customer)
        await db_session.commit()

        builder = TasteProfileBuilder(db_session)

        with patch(
            "app.services.intelligence.taste_profile_builder.vector_store"
        ) as mock_vs:
            mock_vs.is_connected = False

            result = await builder.build_taste_profile(customer.id)

        assert result is None

    async def test_quantity_multiplier_effect(self, db_session):
        """Should weight items by quantity ordered"""
        # This test verifies that ordering 3x of an item weights it 3x more

        brand = Brand(name="Thai Food", slug="thai-food", cuisine_type="Thai")
        db_session.add(brand)
        await db_session.commit()
        await db_session.refresh(brand)

        customer = Customer(
            external_id="test-005",
            email="test5@example.com",
        )
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(customer)

        item = MenuItem(
            brand_id=brand.id,
            name="Pad Thai",
            category="Main",
            cuisine_type="Thai",
            price=10.00,
            is_available=True,
            embedding_id=str(uuid4()),
        )
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        now = datetime.now(timezone.utc)
        order = Order(
            external_id="order-201",
            customer_id=customer.id,
            brand_id=brand.id,
            order_date=now,
            total_amount=30.00,
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        # Quantity = 3
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=item.id,
            item_name="Pad Thai",
            quantity=3,
            unit_price=10.00,
            subtotal=30.00,
        )
        db_session.add(order_item)
        await db_session.commit()

        builder = TasteProfileBuilder(db_session)

        embedding = [1.0] * VECTOR_DIMENSION

        mock_point = MagicMock()
        mock_point.vector = embedding

        with patch(
            "app.services.intelligence.taste_profile_builder.vector_store"
        ) as mock_vs:
            mock_vs.is_connected = True
            mock_vs.get_point = AsyncMock(return_value=mock_point)
            mock_vs.upsert_points = AsyncMock(return_value=True)

            result = await builder.build_taste_profile(customer.id)

        assert result is not None
        assert result["status"] == "success"

        # Total weight should be ~3.0 (quantity=3, recency_weight≈1.0)
        assert result["total_weight"] == pytest.approx(3.0, abs=0.1)


@pytest.mark.asyncio
class TestTasteProfileRetrieval:
    """Tests for retrieving taste profiles"""

    async def test_get_taste_profile_exists(self, db_session):
        """Should retrieve existing taste profile"""
        customer_id = uuid4()

        builder = TasteProfileBuilder(db_session)

        mock_point = MagicMock()
        mock_point.vector = [0.5] * VECTOR_DIMENSION
        mock_point.payload = {"last_updated": "2024-02-09T12:00:00Z"}

        with patch(
            "app.services.intelligence.taste_profile_builder.vector_store"
        ) as mock_vs:
            mock_vs.is_connected = True
            mock_vs.get_point = AsyncMock(return_value=mock_point)

            result = await builder.get_taste_profile(customer_id)

        assert result is not None
        assert result["customer_id"] == str(customer_id)
        assert len(result["vector"]) == VECTOR_DIMENSION
        assert result["last_updated"] == "2024-02-09T12:00:00Z"

    async def test_get_taste_profile_not_found(self, db_session):
        """Should return None if profile doesn't exist"""
        customer_id = uuid4()

        builder = TasteProfileBuilder(db_session)

        with patch(
            "app.services.intelligence.taste_profile_builder.vector_store"
        ) as mock_vs:
            mock_vs.is_connected = True
            mock_vs.get_point = AsyncMock(return_value=None)

            result = await builder.get_taste_profile(customer_id)

        assert result is None

    async def test_get_taste_profile_vector_store_down(self, db_session):
        """Should return None if vector store is not connected"""
        customer_id = uuid4()

        builder = TasteProfileBuilder(db_session)

        with patch(
            "app.services.intelligence.taste_profile_builder.vector_store"
        ) as mock_vs:
            mock_vs.is_connected = False

            result = await builder.get_taste_profile(customer_id)

        assert result is None


@pytest.mark.asyncio
class TestTasteProfileDeletion:
    """Tests for deleting taste profiles"""

    async def test_delete_taste_profile_success(self, db_session):
        """Should delete taste profile successfully"""
        customer_id = uuid4()

        builder = TasteProfileBuilder(db_session)

        with patch(
            "app.services.intelligence.taste_profile_builder.vector_store"
        ) as mock_vs:
            mock_vs.is_connected = True
            mock_vs.delete_points = AsyncMock(return_value=True)

            result = await builder.delete_taste_profile(customer_id)

        assert result is True

    async def test_delete_taste_profile_failure(self, db_session):
        """Should handle deletion failure"""
        customer_id = uuid4()

        builder = TasteProfileBuilder(db_session)

        with patch(
            "app.services.intelligence.taste_profile_builder.vector_store"
        ) as mock_vs:
            mock_vs.is_connected = True
            mock_vs.delete_points = AsyncMock(return_value=False)

            result = await builder.delete_taste_profile(customer_id)

        assert result is False

    async def test_delete_taste_profile_vector_store_down(self, db_session):
        """Should return False if vector store is not connected"""
        customer_id = uuid4()

        builder = TasteProfileBuilder(db_session)

        with patch(
            "app.services.intelligence.taste_profile_builder.vector_store"
        ) as mock_vs:
            mock_vs.is_connected = False

            result = await builder.delete_taste_profile(customer_id)

        assert result is False
