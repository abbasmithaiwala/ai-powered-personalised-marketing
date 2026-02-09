"""Cuisine preference analyzer with recency weighting"""

from datetime import datetime, timedelta, timezone
from collections import defaultdict
from typing import Dict


class CuisineAnalyzer:
    """Analyze customer cuisine preferences with time decay"""

    # Time decay factors
    RECENT_WINDOW = 30  # days
    MEDIUM_WINDOW = 90  # days
    OLD_WINDOW = 180  # days

    RECENT_WEIGHT = 1.0
    MEDIUM_WEIGHT = 0.7
    OLD_WEIGHT = 0.3

    @staticmethod
    def compute_time_weight(order_date: datetime) -> float:
        """
        Compute time decay weight based on how long ago the order was placed.

        Recent orders (last 30 days): weight = 1.0
        Medium (30-90 days): weight = 0.7
        Old (90-180 days): weight = 0.3
        Very old (>180 days): weight = 0.3
        """
        now = datetime.now(timezone.utc)
        days_ago = (now - order_date).days

        if days_ago <= CuisineAnalyzer.RECENT_WINDOW:
            return CuisineAnalyzer.RECENT_WEIGHT
        elif days_ago <= CuisineAnalyzer.MEDIUM_WINDOW:
            return CuisineAnalyzer.MEDIUM_WEIGHT
        else:
            return CuisineAnalyzer.OLD_WEIGHT

    @staticmethod
    def analyze(order_items_with_dates: list) -> Dict[str, float]:
        """
        Analyze cuisine preferences from order history.

        Args:
            order_items_with_dates: List of tuples (order_date, cuisine_type, quantity)

        Returns:
            Dict of cuisine -> normalized score (0-1), top 5 cuisines only
        """
        if not order_items_with_dates:
            return {}

        # Accumulate weighted counts per cuisine
        cuisine_scores = defaultdict(float)

        for order_date, cuisine_type, quantity in order_items_with_dates:
            if not cuisine_type:
                continue

            # Normalize cuisine name (lowercase, strip whitespace)
            cuisine = cuisine_type.lower().strip()

            # Apply time decay weight
            time_weight = CuisineAnalyzer.compute_time_weight(order_date)

            # Weight by quantity ordered
            cuisine_scores[cuisine] += time_weight * quantity

        if not cuisine_scores:
            return {}

        # Normalize scores to 0-1 range
        max_score = max(cuisine_scores.values())
        normalized_scores = {
            cuisine: score / max_score
            for cuisine, score in cuisine_scores.items()
        }

        # Keep only top 5 cuisines
        top_cuisines = sorted(
            normalized_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return dict(top_cuisines)
