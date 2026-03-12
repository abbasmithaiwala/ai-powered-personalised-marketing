"""
Unit tests for preference computation engine.
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.services.intelligence.cuisine_analyzer import CuisineAnalyzer
from app.services.intelligence.dietary_analyzer import DietaryAnalyzer
from app.services.intelligence.price_analyzer import PriceAnalyzer
from app.services.intelligence.timing_analyzer import TimingAnalyzer


class TestCuisineAnalyzer:
    """Tests for cuisine preference analysis"""

    def test_empty_data(self):
        """Should return empty dict for no data"""
        result = CuisineAnalyzer.analyze([])
        assert result == {}

    def test_single_cuisine(self):
        """Should return single cuisine with score 1.0"""
        now = datetime.now(timezone.utc)
        data = [(now, "Italian", 1)]
        result = CuisineAnalyzer.analyze(data)
        assert "italian" in result
        assert result["italian"] == 1.0

    def test_recency_weighting(self):
        """Should weight recent orders higher"""
        now = datetime.now(timezone.utc)
        recent = now - timedelta(days=15)
        medium = now - timedelta(days=60)
        old = now - timedelta(days=150)

        data = [
            (recent, "Italian", 1),
            (medium, "Thai", 1),
            (old, "Chinese", 1),
        ]

        result = CuisineAnalyzer.analyze(data)

        # Recent should score highest (weight 1.0)
        # Medium should score middle (weight 0.7)
        # Old should score lowest (weight 0.3)
        assert result["italian"] > result["thai"]
        assert result["thai"] > result["chinese"]

    def test_quantity_weighting(self):
        """Should weight by quantity ordered"""
        now = datetime.now(timezone.utc)
        data = [
            (now, "Italian", 5),
            (now, "Thai", 1),
        ]

        result = CuisineAnalyzer.analyze(data)
        assert result["italian"] > result["thai"]

    def test_top_5_limit(self):
        """Should return only top 5 cuisines"""
        now = datetime.now(timezone.utc)
        data = [
            (now, "Italian", 10),
            (now, "Thai", 9),
            (now, "Chinese", 8),
            (now, "Mexican", 7),
            (now, "Indian", 6),
            (now, "Japanese", 5),
            (now, "French", 4),
        ]

        result = CuisineAnalyzer.analyze(data)
        assert len(result) == 5
        assert "italian" in result
        assert "french" not in result

    def test_none_cuisine_ignored(self):
        """Should ignore items with no cuisine"""
        now = datetime.now(timezone.utc)
        data = [
            (now, "Italian", 1),
            (now, None, 5),
            (now, "", 3),
        ]

        result = CuisineAnalyzer.analyze(data)
        assert len(result) == 1
        assert "italian" in result


class TestDietaryAnalyzer:
    """Tests for dietary flag detection"""

    def test_empty_data(self):
        """Should return empty dict for no data"""
        result = DietaryAnalyzer.analyze([])
        assert result == {}

    def test_vegetarian_detection(self):
        """Should detect vegetarian diet"""
        now = datetime.now(timezone.utc)
        data = [
            (now, ["vegetarian"]),
            (now, ["vegetarian"]),
            (now, ["vegetarian"]),
            (now, ["vegetarian"]),
            (now, ["vegetarian"]),
        ]

        result = DietaryAnalyzer.analyze(data)
        assert result.get("vegetarian") is True

    def test_below_threshold(self):
        """Should not flag diet below 80% threshold"""
        now = datetime.now(timezone.utc)
        data = [
            (now, ["vegetarian"]),
            (now, ["vegetarian"]),
            (now, ["vegetarian"]),
            (now, []),
            (now, []),
        ]

        result = DietaryAnalyzer.analyze(data)
        # 3/5 = 60%, below 80% threshold
        assert result.get("vegetarian") is False

    def test_multiple_dietary_flags(self):
        """Should detect multiple dietary flags"""
        now = datetime.now(timezone.utc)
        data = [
            (now, ["vegetarian", "gluten_free"]),
            (now, ["vegetarian", "gluten_free"]),
            (now, ["vegetarian", "gluten_free"]),
            (now, ["vegetarian", "gluten_free"]),
            (now, ["vegetarian", "gluten_free"]),
        ]

        result = DietaryAnalyzer.analyze(data)
        assert result.get("vegetarian") is True
        assert result.get("gluten_free") is True

    def test_tag_normalization(self):
        """Should normalize dietary tags"""
        now = datetime.now(timezone.utc)
        # Need 80% threshold, so 4 out of 5 items with vegetarian
        data = [
            (now, ["Vegetarian"]),
            (now, ["VEGETARIAN"]),
            (now, ["vegetarian"]),
            (now, ["vegetarian"]),
            (now, ["gluten-free", "Gluten Free"]),
        ]

        result = DietaryAnalyzer.analyze(data)
        assert result.get("vegetarian") is True
        # Gluten free only appears once, so won't meet threshold
        assert result.get("gluten_free") is False

    def test_recent_orders_only(self):
        """Should prioritize recent orders (last 90 days)"""
        now = datetime.now(timezone.utc)
        recent = now - timedelta(days=30)
        old = now - timedelta(days=180)

        # Recent orders are vegetarian, old orders are not
        data = [
            (recent, ["vegetarian"]),
            (recent, ["vegetarian"]),
            (recent, ["vegetarian"]),
            (recent, ["vegetarian"]),
            (recent, ["vegetarian"]),
            (old, []),
            (old, []),
            (old, []),
            (old, []),
            (old, []),
        ]

        result = DietaryAnalyzer.analyze(data)
        # Should only consider recent orders
        assert result.get("vegetarian") is True


class TestPriceAnalyzer:
    """Tests for price sensitivity analysis"""

    def test_empty_data(self):
        """Should return medium for no data"""
        result = PriceAnalyzer.analyze([])
        assert result == "medium"

    def test_low_sensitivity(self):
        """Should detect low price sensitivity (<₹500)"""
        order_totals = [350.0, 420.0, 480.0, 390.0, 450.0]
        result = PriceAnalyzer.analyze(order_totals)
        assert result == "low"

    def test_medium_sensitivity(self):
        """Should detect medium price sensitivity (₹500-2000)"""
        order_totals = [600.0, 850.0, 1200.0, 1500.0, 1800.0]
        result = PriceAnalyzer.analyze(order_totals)
        assert result == "medium"

    def test_high_sensitivity(self):
        """Should detect high price sensitivity (>₹2000)"""
        order_totals = [2100.0, 2500.0, 3000.0, 4500.0, 5000.0]
        result = PriceAnalyzer.analyze(order_totals)
        assert result == "high"

    def test_boundary_values(self):
        """Should handle boundary values correctly"""
        # Exactly ₹500 average should be medium
        assert PriceAnalyzer.analyze([500.0]) == "medium"

        # Exactly ₹2000 average should be medium
        assert PriceAnalyzer.analyze([2000.0]) == "medium"

        # Just under ₹500 should be low
        assert PriceAnalyzer.analyze([499.99]) == "low"

        # Just over ₹2000 should be high
        assert PriceAnalyzer.analyze([2000.01]) == "high"


class TestTimingAnalyzer:
    """Tests for order timing pattern analysis"""

    def test_empty_data(self):
        """Should return empty dict for no dates"""
        result = TimingAnalyzer.compute_preferred_order_times([])
        assert result == {}

    def test_order_frequency_daily(self):
        """Should detect daily ordering (>20/month)"""
        now = datetime.now(timezone.utc)
        # 25 orders in 30 days
        dates = [now - timedelta(days=i) for i in range(25)]
        result = TimingAnalyzer.compute_order_frequency(dates)
        assert result == "daily"

    def test_order_frequency_weekly(self):
        """Should detect weekly ordering (4-20/month)"""
        now = datetime.now(timezone.utc)
        # 8 orders in 30 days
        dates = [now - timedelta(days=i * 4) for i in range(8)]
        result = TimingAnalyzer.compute_order_frequency(dates)
        assert result == "weekly"

    def test_order_frequency_monthly(self):
        """Should detect monthly ordering (1-4/month)"""
        now = datetime.now(timezone.utc)
        # 2 orders in 30 days
        dates = [now - timedelta(days=i * 15) for i in range(2)]
        result = TimingAnalyzer.compute_order_frequency(dates)
        assert result == "monthly"

    def test_order_frequency_occasional(self):
        """Should detect occasional ordering (<1/month)"""
        now = datetime.now(timezone.utc)
        # 2 orders spread over 150 days = ~0.4 orders/month
        dates = [now - timedelta(days=30), now - timedelta(days=150)]
        result = TimingAnalyzer.compute_order_frequency(dates)
        assert result == "occasional"

    def test_breakfast_time(self):
        """Should detect breakfast orders (6-11)"""
        now = datetime.now(timezone.utc)
        breakfast_time = now.replace(hour=8, minute=30)
        dates = [breakfast_time] * 10

        result = TimingAnalyzer.compute_preferred_order_times(dates)
        assert result["breakfast"] == 1.0

    def test_lunch_time(self):
        """Should detect lunch orders (11-15)"""
        now = datetime.now(timezone.utc)
        lunch_time = now.replace(hour=12, minute=30)
        dates = [lunch_time] * 10

        result = TimingAnalyzer.compute_preferred_order_times(dates)
        assert result["lunch"] == 1.0

    def test_dinner_time(self):
        """Should detect dinner orders (17-22)"""
        now = datetime.now(timezone.utc)
        dinner_time = now.replace(hour=19, minute=30)
        dates = [dinner_time] * 10

        result = TimingAnalyzer.compute_preferred_order_times(dates)
        assert result["dinner"] == 1.0

    def test_late_night_time(self):
        """Should detect late night orders (22-6)"""
        now = datetime.now(timezone.utc)
        late_time = now.replace(hour=23, minute=30)
        dates = [late_time] * 10

        result = TimingAnalyzer.compute_preferred_order_times(dates)
        assert result["late_night"] == 1.0

    def test_mixed_times(self):
        """Should distribute scores across time periods"""
        now = datetime.now(timezone.utc)
        dates = [
            now.replace(hour=8),   # breakfast
            now.replace(hour=8),   # breakfast
            now.replace(hour=12),  # lunch
            now.replace(hour=19),  # dinner
            now.replace(hour=19),  # dinner
            now.replace(hour=19),  # dinner
        ]

        result = TimingAnalyzer.compute_preferred_order_times(dates)

        assert result["breakfast"] == pytest.approx(2/6)
        assert result["lunch"] == pytest.approx(1/6)
        assert result["dinner"] == pytest.approx(3/6)
