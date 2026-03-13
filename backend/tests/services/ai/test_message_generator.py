"""Unit tests for message generator service."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4
from datetime import datetime, timezone, timedelta
import json

from app.services.ai.message_generator import (
    MessageGenerator,
    MessageGenerationException,
    CustomerNotFoundError,
    InsufficientDataError,
)
from app.schemas.message import (
    GeneratedMessage,
    MessageGenerationRequest,
    MessageGenerationResponse,
)
from app.schemas.recommendation import RecommendationItem
from app.models import Customer, Order, OrderItem
from app.services.ai.openrouter_client import (
    OpenRouterAPIKeyError,
    OpenRouterError,
)


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return AsyncMock()


@pytest.fixture
def message_generator(mock_db):
    """Create MessageGenerator with mock DB."""
    return MessageGenerator(mock_db)


@pytest.fixture
def sample_customer():
    """Create a sample customer."""
    customer = Customer(
        id=uuid4(),
        external_id="CUST123",
        email="john@example.com",
        first_name="John",
        last_name="Doe",
        city="Ahmedabad",
        total_orders=5,
        total_spend=150.00,
        first_order_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        last_order_at=datetime(2024, 2, 1, tzinfo=timezone.utc),
    )
    return customer


@pytest.fixture
def sample_order(sample_customer):
    """Create a sample order with items."""
    order = Order(
        id=uuid4(),
        external_id="ORD123",
        customer_id=sample_customer.id,
        brand_id=uuid4(),
        order_date=datetime.now(timezone.utc) - timedelta(days=7),
        total_amount=35.50,
    )

    # Add order items
    order.order_items = [
        OrderItem(
            id=uuid4(),
            order_id=order.id,
            item_name="Margherita Pizza",
            quantity=1,
            unit_price=12.00,
            subtotal=12.00,
        ),
        OrderItem(
            id=uuid4(),
            order_id=order.id,
            item_name="Caesar Salad",
            quantity=1,
            unit_price=8.50,
            subtotal=8.50,
        ),
        OrderItem(
            id=uuid4(),
            order_id=order.id,
            item_name="Tiramisu",
            quantity=1,
            unit_price=6.00,
            subtotal=6.00,
        ),
    ]

    return order


@pytest.fixture
def sample_recommendations():
    """Create sample recommendations."""
    return [
        RecommendationItem(
            menu_item_id=uuid4(),
            name="Quattro Formaggi Pizza",
            brand_name="Pizza Palace",
            brand_id=uuid4(),
            category="mains",
            cuisine_type="italian",
            price=14.50,
            score=0.92,
            reason="Matches your preference for Italian cuisine",
        ),
        RecommendationItem(
            menu_item_id=uuid4(),
            name="Penne Arrabbiata",
            brand_name="Pizza Palace",
            brand_id=uuid4(),
            category="mains",
            cuisine_type="italian",
            price=13.00,
            score=0.88,
            reason="You love Italian pasta dishes",
        ),
        RecommendationItem(
            menu_item_id=uuid4(),
            name="Caprese Salad",
            brand_name="Pizza Palace",
            brand_id=uuid4(),
            category="starters",
            cuisine_type="italian",
            price=7.50,
            score=0.85,
            reason="Perfect starter for Italian meal",
        ),
    ]


@pytest.fixture
def sample_request(sample_customer):
    """Create a sample message generation request."""
    return MessageGenerationRequest(
        customer_id=sample_customer.id,
        campaign_purpose="Weekend special - New Italian menu items",
        brand_group_name="Pizza Palace",
        offer="20% off your next order",
        recommendation_limit=5,
    )


@pytest.fixture
def sample_llm_response():
    """Create a sample LLM JSON response."""
    return json.dumps(
        {
            "subject": "John, try our new Italian dishes this weekend! 🍕",
            "body": "Hi John, we noticed you love Italian cuisine! This weekend, "
            "enjoy 20% off when you try our new Quattro Formaggi Pizza and "
            "Penne Arrabbiata. Based on your recent Margherita Pizza order, "
            "we think you'll love these authentic Italian flavors. "
            "Order now and taste the difference!",
        }
    )


class TestMessageGeneratorGetCustomer:
    """Test customer fetching."""

    @pytest.mark.asyncio
    async def test_get_customer_success(
        self, message_generator, mock_db, sample_customer
    ):
        """Test successfully fetching a customer."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_customer
        mock_db.execute = AsyncMock(return_value=mock_result)

        customer = await message_generator._get_customer(sample_customer.id)

        assert customer.id == sample_customer.id
        assert customer.first_name == "John"

    @pytest.mark.asyncio
    async def test_get_customer_not_found(self, message_generator, mock_db):
        """Test customer not found raises error."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        customer_id = uuid4()

        with pytest.raises(CustomerNotFoundError) as exc_info:
            await message_generator._get_customer(customer_id)

        assert str(customer_id) in str(exc_info.value)


class TestMessageGeneratorGetRecommendations:
    """Test recommendation fetching."""

    @pytest.mark.asyncio
    async def test_get_recommendations_success(
        self, message_generator, sample_customer, sample_recommendations
    ):
        """Test successfully fetching recommendations."""
        message_generator.recommendation_engine.generate_recommendations = AsyncMock(
            return_value=(sample_recommendations, False)
        )

        recommendations = await message_generator._get_recommendations(
            sample_customer.id, 5
        )

        assert len(recommendations) == 3
        assert recommendations[0].name == "Quattro Formaggi Pizza"

    @pytest.mark.asyncio
    async def test_get_recommendations_empty(self, message_generator, sample_customer):
        """Test when no recommendations available."""
        message_generator.recommendation_engine.generate_recommendations = AsyncMock(
            return_value=([], True)
        )

        with pytest.raises(InsufficientDataError) as exc_info:
            await message_generator._get_recommendations(sample_customer.id, 5)

        assert "No recommendations available" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_recommendations_engine_error(
        self, message_generator, sample_customer
    ):
        """Test when recommendation engine raises ValueError."""
        message_generator.recommendation_engine.generate_recommendations = AsyncMock(
            side_effect=ValueError("Customer profile not found")
        )

        with pytest.raises(InsufficientDataError):
            await message_generator._get_recommendations(sample_customer.id, 5)


class TestMessageGeneratorGetLastOrderSummary:
    """Test last order summary generation."""

    @pytest.mark.asyncio
    async def test_get_last_order_summary_success(
        self, message_generator, mock_db, sample_customer, sample_order
    ):
        """Test getting last order summary."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_order
        mock_db.execute = AsyncMock(return_value=mock_result)

        summary = await message_generator._get_last_order_summary(sample_customer.id)

        assert "Margherita Pizza" in summary
        assert "Caesar Salad" in summary
        assert "Tiramisu" in summary
        assert "ago" in summary or "today" in summary

    @pytest.mark.asyncio
    async def test_get_last_order_summary_no_orders(
        self, message_generator, mock_db, sample_customer
    ):
        """Test when customer has no orders."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        summary = await message_generator._get_last_order_summary(sample_customer.id)

        assert "hasn't ordered yet" in summary


class TestMessageGeneratorParseLLMResponse:
    """Test LLM response parsing."""

    def test_parse_valid_json(self, message_generator, sample_llm_response):
        """Test parsing valid JSON response."""
        message = message_generator._parse_llm_response(sample_llm_response)

        assert isinstance(message, GeneratedMessage)
        assert "John" in message.subject
        assert len(message.subject) <= 60
        word_count = len(message.body.split())
        assert word_count <= 150

    def test_parse_invalid_json(self, message_generator):
        """Test parsing invalid JSON raises error."""
        invalid_json = "This is not valid JSON {subject:"

        with pytest.raises(MessageGenerationException) as exc_info:
            message_generator._parse_llm_response(invalid_json)

        assert "invalid json" in str(exc_info.value).lower()

    def test_parse_missing_fields(self, message_generator):
        """Test parsing JSON with missing required fields."""
        invalid_response = json.dumps({"subject": "Only subject, no body"})

        with pytest.raises(MessageGenerationException) as exc_info:
            message_generator._parse_llm_response(invalid_response)

        assert "validation" in str(exc_info.value).lower()

    def test_parse_subject_too_long(self, message_generator):
        """Test parsing JSON with subject exceeding 60 chars."""
        invalid_response = json.dumps(
            {
                "subject": "This is a very long subject line that exceeds the sixty character limit",
                "body": "Short body",
            }
        )

        with pytest.raises(MessageGenerationException):
            message_generator._parse_llm_response(invalid_response)

    def test_parse_body_too_long(self, message_generator):
        """Test parsing JSON with body exceeding 150 words."""
        long_body = " ".join(["word"] * 151)  # 151 words
        invalid_response = json.dumps({"subject": "Subject", "body": long_body})

        with pytest.raises(MessageGenerationException):
            message_generator._parse_llm_response(invalid_response)


class TestMessageGeneratorGenerateMessage:
    """Test full message generation flow."""

    @pytest.mark.asyncio
    async def test_generate_message_success(
        self,
        message_generator,
        mock_db,
        sample_customer,
        sample_order,
        sample_recommendations,
        sample_request,
        sample_llm_response,
    ):
        """Test successful message generation."""
        # Mock customer fetch
        mock_customer_result = Mock()
        mock_customer_result.scalar_one_or_none.return_value = sample_customer

        # Mock order fetch
        mock_order_result = Mock()
        mock_order_result.scalar_one_or_none.return_value = sample_order

        mock_db.execute = AsyncMock(
            side_effect=[mock_customer_result, mock_order_result]
        )

        # Mock recommendations
        message_generator.recommendation_engine.generate_recommendations = AsyncMock(
            return_value=(sample_recommendations, False)
        )

        # Mock OpenRouter client
        with patch(
            "app.services.ai.message_generator.OpenRouterClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.complete = AsyncMock(return_value=sample_llm_response)
            mock_client.model = "anthropic/claude-3.5-sonnet"
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            response = await message_generator.generate_message(sample_request)

            # Verify response structure
            assert isinstance(response, MessageGenerationResponse)
            assert response.customer_id == sample_customer.id
            assert "John" in response.message.subject
            assert len(response.recommendations_used) == 3
            assert response.model_used == "anthropic/claude-3.5-sonnet"

            # Verify LLM was called with correct prompts
            mock_client.complete.assert_called_once()
            call_args = mock_client.complete.call_args
            messages = call_args.kwargs["messages"]

            assert len(messages) == 2
            assert messages[0]["role"] == "system"
            assert "Pizza Palace" in messages[0]["content"]
            assert messages[1]["role"] == "user"
            assert "John" in messages[1]["content"]
            assert "Quattro Formaggi Pizza" in messages[1]["content"]

    @pytest.mark.asyncio
    async def test_generate_message_customer_not_found(
        self, message_generator, mock_db, sample_request
    ):
        """Test message generation when customer doesn't exist."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(CustomerNotFoundError):
            await message_generator.generate_message(sample_request)

    @pytest.mark.asyncio
    async def test_generate_message_no_recommendations(
        self, message_generator, mock_db, sample_customer, sample_request
    ):
        """Test message generation when no recommendations available."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_customer
        mock_db.execute = AsyncMock(return_value=mock_result)

        message_generator.recommendation_engine.generate_recommendations = AsyncMock(
            return_value=([], True)
        )

        with pytest.raises(InsufficientDataError):
            await message_generator.generate_message(sample_request)

    @pytest.mark.asyncio
    async def test_generate_message_api_key_error(
        self,
        message_generator,
        mock_db,
        sample_customer,
        sample_order,
        sample_recommendations,
        sample_request,
    ):
        """Test message generation when API key is missing."""
        # Mock DB responses
        mock_customer_result = Mock()
        mock_customer_result.scalar_one_or_none.return_value = sample_customer
        mock_order_result = Mock()
        mock_order_result.scalar_one_or_none.return_value = sample_order
        mock_db.execute = AsyncMock(
            side_effect=[mock_customer_result, mock_order_result]
        )

        # Mock recommendations
        message_generator.recommendation_engine.generate_recommendations = AsyncMock(
            return_value=(sample_recommendations, False)
        )

        # Mock OpenRouter client to raise API key error
        with patch(
            "app.services.ai.message_generator.OpenRouterClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.complete = AsyncMock(
                side_effect=OpenRouterAPIKeyError("API key not set")
            )
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            with pytest.raises(OpenRouterAPIKeyError):
                await message_generator.generate_message(sample_request)

    @pytest.mark.asyncio
    async def test_generate_message_llm_error(
        self,
        message_generator,
        mock_db,
        sample_customer,
        sample_order,
        sample_recommendations,
        sample_request,
    ):
        """Test message generation when LLM API fails."""
        # Mock DB responses
        mock_customer_result = Mock()
        mock_customer_result.scalar_one_or_none.return_value = sample_customer
        mock_order_result = Mock()
        mock_order_result.scalar_one_or_none.return_value = sample_order
        mock_db.execute = AsyncMock(
            side_effect=[mock_customer_result, mock_order_result]
        )

        # Mock recommendations
        message_generator.recommendation_engine.generate_recommendations = AsyncMock(
            return_value=(sample_recommendations, False)
        )

        # Mock OpenRouter client to raise error
        with patch(
            "app.services.ai.message_generator.OpenRouterClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.complete = AsyncMock(
                side_effect=OpenRouterError("API request failed")
            )
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            with pytest.raises(MessageGenerationException) as exc_info:
                await message_generator.generate_message(sample_request)

            assert "Failed to generate message" in str(exc_info.value)
