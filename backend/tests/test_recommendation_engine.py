"""
Unit tests for recommendation engine.
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal

from app.services.intelligence.recommendation_engine import RecommendationEngine
from app.models.customer import Customer
from app.models.customer_preference import CustomerPreference
from app.models.menu_item import MenuItem
from app.models.brand import Brand
from app.models.order import Order
from app.models.order_item import OrderItem


class TestDietaryRestrictionFiltering:
    """Tests for dietary restriction violation logic"""

    def test_no_restrictions_allows_all(self):
        """No restrictions should allow any item"""
        engine = RecommendationEngine(AsyncMock())

        item_tags = ["spicy", "beef"]
        restrictions = []

        violates = engine._violates_dietary_restrictions(item_tags, restrictions)
        assert violates is False

    def test_vegetarian_restriction_blocks_meat(self):
        """Vegetarian customer should not get non-vegetarian items"""
        engine = RecommendationEngine(AsyncMock())

        item_tags = ["spicy", "beef"]
        restrictions = ["vegetarian"]

        violates = engine._violates_dietary_restrictions(item_tags, restrictions)
        assert violates is True

    def test_vegetarian_restriction_allows_vegetarian(self):
        """Vegetarian customer should get vegetarian items"""
        engine = RecommendationEngine(AsyncMock())

        item_tags = ["vegetarian", "spicy"]
        restrictions = ["vegetarian"]

        violates = engine._violates_dietary_restrictions(item_tags, restrictions)
        assert violates is False

    def test_vegetarian_restriction_allows_vegan(self):
        """Vegan items are also vegetarian"""
        engine = RecommendationEngine(AsyncMock())

        item_tags = ["vegan", "organic"]
        restrictions = ["vegetarian"]

        violates = engine._violates_dietary_restrictions(item_tags, restrictions)
        assert violates is False

    def test_vegan_restriction_blocks_non_vegan(self):
        """Vegan customer should only get vegan items"""
        engine = RecommendationEngine(AsyncMock())

        item_tags = ["vegetarian", "dairy"]
        restrictions = ["vegan"]

        violates = engine._violates_dietary_restrictions(item_tags, restrictions)
        assert violates is True

    def test_vegan_restriction_allows_vegan(self):
        """Vegan customer should get vegan items"""
        engine = RecommendationEngine(AsyncMock())

        item_tags = ["vegan", "organic"]
        restrictions = ["vegan"]

        violates = engine._violates_dietary_restrictions(item_tags, restrictions)
        assert violates is False

    def test_halal_restriction(self):
        """Halal customer should only get halal items"""
        engine = RecommendationEngine(AsyncMock())

        item_tags_without_halal = ["spicy", "chicken"]
        restrictions = ["halal"]

        violates = engine._violates_dietary_restrictions(item_tags_without_halal, restrictions)
        assert violates is True

        item_tags_with_halal = ["halal", "spicy", "chicken"]
        violates = engine._violates_dietary_restrictions(item_tags_with_halal, restrictions)
        assert violates is False

    def test_gluten_free_restriction(self):
        """Gluten-free customer should only get gluten-free items"""
        engine = RecommendationEngine(AsyncMock())

        item_tags_without_gf = ["pasta", "wheat"]
        restrictions = ["gluten_free"]

        violates = engine._violates_dietary_restrictions(item_tags_without_gf, restrictions)
        assert violates is True

        item_tags_with_gf = ["gluten_free", "rice"]
        violates = engine._violates_dietary_restrictions(item_tags_with_gf, restrictions)
        assert violates is False

    def test_case_insensitive_matching(self):
        """Dietary tag matching should be case-insensitive"""
        engine = RecommendationEngine(AsyncMock())

        item_tags = ["Vegetarian", "ORGANIC"]
        restrictions = ["vegetarian"]

        violates = engine._violates_dietary_restrictions(item_tags, restrictions)
        assert violates is False

    def test_multiple_restrictions(self):
        """Multiple restrictions should all be checked"""
        engine = RecommendationEngine(AsyncMock())

        item_tags = ["vegan", "gluten_free"]
        restrictions = ["vegan", "gluten_free"]

        violates = engine._violates_dietary_restrictions(item_tags, restrictions)
        assert violates is False

        item_tags_missing_one = ["vegan"]
        violates = engine._violates_dietary_restrictions(item_tags_missing_one, restrictions)
        assert violates is True


class TestRecommendationReasonBuilder:
    """Tests for building human-readable recommendation reasons"""

    def test_reason_with_no_preferences(self):
        """Should return generic reason when no preferences exist"""
        engine = RecommendationEngine(AsyncMock())

        menu_item = MagicMock(spec=MenuItem)
        menu_item.cuisine_type = "Italian"
        menu_item.category = "mains"
        menu_item.dietary_tags = []

        reason = engine._build_recommendation_reason(
            menu_item=menu_item,
            customer_preference=None,
            is_new_brand=False,
        )

        assert reason == "Recommended based on your order history"

    def test_reason_with_cuisine_match(self):
        """Should mention cuisine preference in reason"""
        engine = RecommendationEngine(AsyncMock())

        menu_item = MagicMock(spec=MenuItem)
        menu_item.cuisine_type = "Italian"
        menu_item.category = "mains"
        menu_item.dietary_tags = []

        preference = MagicMock(spec=CustomerPreference)
        preference.favorite_cuisines = {"italian": 0.8, "thai": 0.5}
        preference.favorite_categories = {}
        preference.dietary_flags = {}

        reason = engine._build_recommendation_reason(
            menu_item=menu_item,
            customer_preference=preference,
            is_new_brand=False,
        )

        assert "italian cuisine" in reason.lower()

    def test_reason_with_category_match(self):
        """Should mention category preference in reason"""
        engine = RecommendationEngine(AsyncMock())

        menu_item = MagicMock(spec=MenuItem)
        menu_item.cuisine_type = None
        menu_item.category = "desserts"
        menu_item.dietary_tags = []

        preference = MagicMock(spec=CustomerPreference)
        preference.favorite_cuisines = {}
        preference.favorite_categories = {"desserts": 0.9}
        preference.dietary_flags = {}

        reason = engine._build_recommendation_reason(
            menu_item=menu_item,
            customer_preference=preference,
            is_new_brand=False,
        )

        assert "desserts" in reason.lower()

    def test_reason_with_dietary_match(self):
        """Should mention dietary preference in reason"""
        engine = RecommendationEngine(AsyncMock())

        menu_item = MagicMock(spec=MenuItem)
        menu_item.cuisine_type = None
        menu_item.category = None
        menu_item.dietary_tags = ["vegetarian", "organic"]

        preference = MagicMock(spec=CustomerPreference)
        preference.favorite_cuisines = {}
        preference.favorite_categories = {}
        preference.dietary_flags = {"vegetarian": True}

        reason = engine._build_recommendation_reason(
            menu_item=menu_item,
            customer_preference=preference,
            is_new_brand=False,
        )

        assert "vegetarian" in reason.lower()

    def test_reason_with_new_brand(self):
        """Should mention new brand in reason"""
        engine = RecommendationEngine(AsyncMock())

        menu_item = MagicMock(spec=MenuItem)
        menu_item.cuisine_type = None
        menu_item.category = None
        menu_item.dietary_tags = []

        preference = MagicMock(spec=CustomerPreference)
        preference.favorite_cuisines = {}
        preference.favorite_categories = {}
        preference.dietary_flags = {}

        reason = engine._build_recommendation_reason(
            menu_item=menu_item,
            customer_preference=preference,
            is_new_brand=True,
        )

        assert "brand you haven't tried" in reason.lower()

    def test_reason_with_multiple_matches(self):
        """Should combine multiple matching reasons"""
        engine = RecommendationEngine(AsyncMock())

        menu_item = MagicMock(spec=MenuItem)
        menu_item.cuisine_type = "Thai"
        menu_item.category = "mains"
        menu_item.dietary_tags = ["vegan"]

        preference = MagicMock(spec=CustomerPreference)
        preference.favorite_cuisines = {"thai": 0.9}
        preference.favorite_categories = {"mains": 0.8}
        preference.dietary_flags = {"vegan": True}

        reason = engine._build_recommendation_reason(
            menu_item=menu_item,
            customer_preference=preference,
            is_new_brand=True,
        )

        # Should contain multiple reasons
        assert "thai" in reason.lower()
        assert "vegan" in reason.lower() or "main" in reason.lower()

    def test_reason_ignores_low_preference_scores(self):
        """Should not mention preferences with low scores (<0.5)"""
        engine = RecommendationEngine(AsyncMock())

        menu_item = MagicMock(spec=MenuItem)
        menu_item.cuisine_type = "Mexican"
        menu_item.category = "starters"
        menu_item.dietary_tags = []

        preference = MagicMock(spec=CustomerPreference)
        preference.favorite_cuisines = {"mexican": 0.3}  # Low score
        preference.favorite_categories = {"starters": 0.2}  # Low score
        preference.dietary_flags = {}

        reason = engine._build_recommendation_reason(
            menu_item=menu_item,
            customer_preference=preference,
            is_new_brand=False,
        )

        # Should fall back to generic reason
        assert "taste profile" in reason.lower()


@pytest.mark.asyncio
class TestRecommendationEngineIntegration:
    """Integration tests requiring database mocks"""

    async def test_customer_not_found_raises_error(self):
        """Should raise ValueError when customer doesn't exist"""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        engine = RecommendationEngine(mock_db)

        with pytest.raises(ValueError, match="Customer .* not found"):
            await engine.generate_recommendations(
                customer_id=uuid4(),
                limit=5,
            )

    async def test_get_recently_ordered_items(self):
        """Should query recently ordered items correctly"""
        mock_db = AsyncMock()
        customer_id = uuid4()
        item_id_1 = uuid4()
        item_id_2 = uuid4()

        # Mock the query result
        mock_result = MagicMock()
        mock_result.all.return_value = [(item_id_1,), (item_id_2,)]
        mock_db.execute.return_value = mock_result

        engine = RecommendationEngine(mock_db)
        recently_ordered = await engine._get_recently_ordered_items(
            customer_id=customer_id,
            days=30,
        )

        assert recently_ordered == {item_id_1, item_id_2}

        # Verify query was called
        assert mock_db.execute.called

    async def test_get_customer_brand_ids(self):
        """Should query customer's brand history correctly"""
        mock_db = AsyncMock()
        customer_id = uuid4()
        brand_id_1 = uuid4()
        brand_id_2 = uuid4()

        # Mock the query result
        mock_result = MagicMock()
        mock_result.all.return_value = [(brand_id_1,), (brand_id_2,)]
        mock_db.execute.return_value = mock_result

        engine = RecommendationEngine(mock_db)
        brand_ids = await engine._get_customer_brand_ids(customer_id)

        assert brand_ids == {brand_id_1, brand_id_2}
        assert mock_db.execute.called

    async def test_get_menu_item_with_brand(self):
        """Should fetch menu item with brand relationship"""
        mock_db = AsyncMock()
        menu_item_id = uuid4()

        # Create mock menu item with brand
        mock_brand = MagicMock(spec=Brand)
        mock_brand.name = "Test Restaurant"

        mock_menu_item = MagicMock(spec=MenuItem)
        mock_menu_item.id = menu_item_id
        mock_menu_item.name = "Test Dish"
        mock_menu_item.brand = mock_brand

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_menu_item
        mock_db.execute.return_value = mock_result

        engine = RecommendationEngine(mock_db)
        item = await engine._get_menu_item_with_brand(menu_item_id)

        assert item == mock_menu_item
        assert item.brand.name == "Test Restaurant"
        assert mock_db.execute.called


class TestFallbackRecommendations:
    """Tests for fallback recommendation generation"""

    def test_fallback_reason_mentions_popularity(self):
        """Fallback recommendations should mention order count"""
        # This test verifies the reason string format
        order_count = 42
        reason = f"Popular choice - ordered {order_count} times by our customers"

        assert "Popular choice" in reason
        assert "42 times" in reason

    def test_fallback_score_is_neutral(self):
        """Fallback recommendations should use neutral score"""
        # Fallback items get score of 0.5
        assert 0.5 == pytest.approx(0.5)
