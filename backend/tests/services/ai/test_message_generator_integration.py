"""Integration tests for message generator with real database."""

import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock
import json

from app.services.ai.message_generator import (
    MessageGenerator,
    CustomerNotFoundError,
    InsufficientDataError,
)
from app.schemas.message import MessageGenerationRequest
from app.models import Customer, Brand, MenuItem, Order, OrderItem, CustomerPreference


@pytest.fixture
async def test_brand(db_session):
    """Create a test brand."""
    brand = Brand(
        id=uuid4(),
        name="Test Italian Restaurant",
        slug="test-italian",
        cuisine_type="italian",
        is_active=True,
    )
    db_session.add(brand)
    await db_session.commit()
    await db_session.refresh(brand)
    return brand


@pytest.fixture
async def test_menu_items(db_session, test_brand):
    """Create test menu items."""
    items = []
    item_data = [
        {
            "name": "Margherita Pizza",
            "category": "mains",
            "cuisine_type": "italian",
            "price": 12.00,
            "dietary_tags": ["vegetarian"],
        },
        {
            "name": "Caesar Salad",
            "category": "starters",
            "cuisine_type": "italian",
            "price": 8.50,
            "dietary_tags": [],
        },
        {
            "name": "Tiramisu",
            "category": "desserts",
            "cuisine_type": "italian",
            "price": 6.00,
            "dietary_tags": ["vegetarian"],
        },
    ]

    for data in item_data:
        item = MenuItem(
            id=uuid4(),
            brand_id=test_brand.id,
            name=data["name"],
            category=data["category"],
            cuisine_type=data["cuisine_type"],
            price=data["price"],
            dietary_tags=data["dietary_tags"],
            is_available=True,
        )
        db_session.add(item)
        items.append(item)

    await db_session.commit()
    for item in items:
        await db_session.refresh(item)

    return items


@pytest.fixture
async def test_customer(db_session):
    """Create a test customer with order history."""
    customer = Customer(
        id=uuid4(),
        external_id="TEST_CUST_001",
        email="test.customer@example.com",
        first_name="Alice",
        last_name="Smith",
        city="Ahmedabad",
        total_orders=3,
        total_spend=75.00,
        first_order_at=datetime.now(timezone.utc) - timedelta(days=30),
        last_order_at=datetime.now(timezone.utc) - timedelta(days=5),
    )
    db_session.add(customer)
    await db_session.commit()
    await db_session.refresh(customer)
    return customer


@pytest.fixture
async def test_orders(db_session, test_customer, test_brand, test_menu_items):
    """Create test orders for the customer."""
    orders = []

    # Order 1 - 30 days ago
    order1 = Order(
        id=uuid4(),
        external_id="TEST_ORD_001",
        customer_id=test_customer.id,
        brand_id=test_brand.id,
        order_date=datetime.now(timezone.utc) - timedelta(days=30),
        total_amount=26.50,
    )
    db_session.add(order1)
    await db_session.flush()

    item1 = OrderItem(
        id=uuid4(),
        order_id=order1.id,
        menu_item_id=test_menu_items[0].id,
        item_name="Margherita Pizza",
        quantity=1,
        unit_price=12.00,
        subtotal=12.00,
    )
    item2 = OrderItem(
        id=uuid4(),
        order_id=order1.id,
        menu_item_id=test_menu_items[1].id,
        item_name="Caesar Salad",
        quantity=1,
        unit_price=8.50,
        subtotal=8.50,
    )
    item3 = OrderItem(
        id=uuid4(),
        order_id=order1.id,
        menu_item_id=test_menu_items[2].id,
        item_name="Tiramisu",
        quantity=1,
        unit_price=6.00,
        subtotal=6.00,
    )
    db_session.add_all([item1, item2, item3])
    orders.append(order1)

    # Order 2 - 15 days ago
    order2 = Order(
        id=uuid4(),
        external_id="TEST_ORD_002",
        customer_id=test_customer.id,
        brand_id=test_brand.id,
        order_date=datetime.now(timezone.utc) - timedelta(days=15),
        total_amount=20.00,
    )
    db_session.add(order2)
    await db_session.flush()

    item4 = OrderItem(
        id=uuid4(),
        order_id=order2.id,
        menu_item_id=test_menu_items[0].id,
        item_name="Margherita Pizza",
        quantity=1,
        unit_price=12.00,
        subtotal=12.00,
    )
    item5 = OrderItem(
        id=uuid4(),
        order_id=order2.id,
        menu_item_id=test_menu_items[1].id,
        item_name="Caesar Salad",
        quantity=1,
        unit_price=8.50,
        subtotal=8.50,
    )
    db_session.add_all([item4, item5])
    orders.append(order2)

    # Order 3 - 5 days ago
    order3 = Order(
        id=uuid4(),
        external_id="TEST_ORD_003",
        customer_id=test_customer.id,
        brand_id=test_brand.id,
        order_date=datetime.now(timezone.utc) - timedelta(days=5),
        total_amount=18.00,
    )
    db_session.add(order3)
    await db_session.flush()

    item6 = OrderItem(
        id=uuid4(),
        order_id=order3.id,
        menu_item_id=test_menu_items[0].id,
        item_name="Margherita Pizza",
        quantity=1,
        unit_price=12.00,
        subtotal=12.00,
    )
    item7 = OrderItem(
        id=uuid4(),
        order_id=order3.id,
        menu_item_id=test_menu_items[2].id,
        item_name="Tiramisu",
        quantity=1,
        unit_price=6.00,
        subtotal=6.00,
    )
    db_session.add_all([item6, item7])
    orders.append(order3)

    await db_session.commit()
    return orders


@pytest.fixture
async def test_customer_with_preference(db_session, test_customer):
    """Create customer preference for test customer."""
    preference = CustomerPreference(
        id=uuid4(),
        customer_id=test_customer.id,
        favorite_cuisines={"italian": 0.9, "mediterranean": 0.5},
        favorite_categories={"mains": 0.8, "desserts": 0.6},
        dietary_flags={"vegetarian": True},
        price_sensitivity="medium",
        order_frequency="weekly",
        preferred_order_times={"dinner": 0.7, "lunch": 0.3},
        last_computed_at=datetime.now(timezone.utc),
        version=1,
    )
    db_session.add(preference)
    await db_session.commit()
    await db_session.refresh(preference)
    return preference


class TestMessageGeneratorIntegration:
    """Integration tests with real database."""

    @pytest.mark.asyncio
    async def test_get_customer_from_db(
        self, db_session, test_customer, test_orders, test_customer_with_preference
    ):
        """Test fetching customer from database."""
        generator = MessageGenerator(db_session)

        customer = await generator._get_customer(test_customer.id)

        assert customer.id == test_customer.id
        assert customer.first_name == "Alice"
        assert customer.email == "test.customer@example.com"

    @pytest.mark.asyncio
    async def test_get_customer_not_found(self, db_session):
        """Test fetching non-existent customer."""
        generator = MessageGenerator(db_session)
        fake_id = uuid4()

        with pytest.raises(CustomerNotFoundError) as exc_info:
            await generator._get_customer(fake_id)

        assert str(fake_id) in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_last_order_summary_from_db(
        self, db_session, test_customer, test_orders
    ):
        """Test getting last order summary from real database."""
        generator = MessageGenerator(db_session)

        summary = await generator._get_last_order_summary(test_customer.id)

        # Should include items from most recent order (5 days ago)
        assert "Margherita Pizza" in summary
        assert "Tiramisu" in summary
        assert "days ago" in summary or "ago" in summary

    @pytest.mark.asyncio
    async def test_get_last_order_summary_no_orders(self, db_session, test_customer):
        """Test last order summary when customer has no orders."""
        generator = MessageGenerator(db_session)

        summary = await generator._get_last_order_summary(test_customer.id)

        assert "hasn't ordered yet" in summary

    @pytest.mark.asyncio
    async def test_generate_message_integration(
        self,
        db_session,
        test_customer,
        test_brand,
        test_menu_items,
        test_orders,
        test_customer_with_preference,
    ):
        """Test full message generation with database and mocked LLM."""
        generator = MessageGenerator(db_session)

        # Mock recommendations (since we don't have embeddings in test DB)
        from app.schemas.recommendation import RecommendationItem

        mock_recommendations = [
            RecommendationItem(
                menu_item_id=test_menu_items[0].id,
                name="Margherita Pizza",
                brand_name=test_brand.name,
                brand_id=test_brand.id,
                category="mains",
                cuisine_type="italian",
                price=12.00,
                score=0.9,
                reason="You love Italian pizza",
            )
        ]

        # Mock LLM response
        mock_llm_response = json.dumps(
            {
                "subject": "Alice, enjoy our special Italian menu this weekend!",
                "body": "Hi Alice, based on your love for Italian cuisine and "
                "recent Margherita Pizza orders, we think you'll love our "
                "special this weekend. Try our authentic Italian dishes with "
                "20% off your next order. Order now!",
            }
        )

        request = MessageGenerationRequest(
            customer_id=test_customer.id,
            campaign_purpose="Weekend Italian special",
            brand_group_name=test_brand.name,
            offer="20% off your next order",
            recommendation_limit=3,
        )

        with patch.object(
            generator.recommendation_engine,
            "generate_recommendations",
            new=AsyncMock(return_value=(mock_recommendations, False)),
        ):
            with patch(
                "app.services.ai.message_generator.OpenRouterClient"
            ) as mock_client_class:
                mock_client = AsyncMock()
                mock_client.complete = AsyncMock(return_value=mock_llm_response)
                mock_client.model = "test-model"
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                response = await generator.generate_message(request)

                # Verify response
                assert response.customer_id == test_customer.id
                assert "Alice" in response.message.subject
                assert len(response.message.subject) <= 60
                assert len(response.message.body.split()) <= 150
                assert len(response.recommendations_used) > 0

                # Verify LLM was called with correct data
                mock_client.complete.assert_called_once()
                call_args = mock_client.complete.call_args
                messages = call_args.kwargs["messages"]

                assert len(messages) == 2
                system_prompt = messages[0]["content"]
                user_prompt = messages[1]["content"]

                assert test_brand.name in system_prompt
                assert "Alice" in user_prompt
                assert "Margherita Pizza" in user_prompt
                assert "20% off" in user_prompt

    @pytest.mark.asyncio
    async def test_generate_message_no_recommendations(
        self, db_session, test_customer, test_orders
    ):
        """Test message generation when recommendations fail."""
        generator = MessageGenerator(db_session)

        request = MessageGenerationRequest(
            customer_id=test_customer.id,
            campaign_purpose="Weekend special",
            brand_group_name="Test Restaurant",
            recommendation_limit=3,
        )

        # Mock empty recommendations
        with patch.object(
            generator.recommendation_engine,
            "generate_recommendations",
            new=AsyncMock(return_value=([], True)),
        ):
            with pytest.raises(InsufficientDataError) as exc_info:
                await generator.generate_message(request)

            assert "No recommendations available" in str(exc_info.value)
