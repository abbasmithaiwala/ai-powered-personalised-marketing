"""Dietary preference analyzer"""

from datetime import datetime, timedelta, timezone
from collections import defaultdict
from typing import Dict, List


class DietaryAnalyzer:
    """Detect dietary flags from order history"""

    # Dietary tags to detect
    DIETARY_FLAGS = ["vegetarian", "vegan", "halal", "gluten_free", "gluten-free"]

    # Threshold: if >80% of recent orders have a dietary tag, flag as that diet
    THRESHOLD = 0.8

    # Consider only recent orders (last 90 days) for dietary analysis
    RECENT_DAYS = 90

    @staticmethod
    def normalize_dietary_tag(tag: str) -> str:
        """Normalize dietary tags to standard format"""
        normalized = tag.lower().strip().replace("-", "_").replace(" ", "_")

        # Map common variations
        if normalized in ["gluten_free", "glutenfree"]:
            return "gluten_free"

        return normalized

    @staticmethod
    def analyze(order_items_with_dates: list) -> Dict[str, bool]:
        """
        Detect dietary flags from order history.

        Args:
            order_items_with_dates: List of tuples (order_date, dietary_tags)
                where dietary_tags is a list of strings

        Returns:
            Dict of dietary_flag -> bool (True if customer follows that diet)
        """
        if not order_items_with_dates:
            return {}

        # Filter to recent orders only
        now = datetime.now(timezone.utc)
        cutoff_date = now - timedelta(days=DietaryAnalyzer.RECENT_DAYS)

        recent_items = [
            (order_date, dietary_tags)
            for order_date, dietary_tags in order_items_with_dates
            if order_date >= cutoff_date
        ]

        if not recent_items:
            # If no recent orders, use all available data
            recent_items = order_items_with_dates

        # Count items with each dietary tag
        dietary_counts = defaultdict(int)
        total_items = len(recent_items)

        for _, dietary_tags in recent_items:
            if not dietary_tags:
                continue

            # Track which dietary flags appear in this item
            item_flags = set()
            for tag in dietary_tags:
                normalized_tag = DietaryAnalyzer.normalize_dietary_tag(tag)
                if normalized_tag in DietaryAnalyzer.DIETARY_FLAGS:
                    item_flags.add(normalized_tag)

            # Count each flag once per item
            for flag in item_flags:
                dietary_counts[flag] += 1

        # Compute percentages and flag if above threshold
        dietary_flags = {}
        for flag in DietaryAnalyzer.DIETARY_FLAGS:
            if flag == "gluten-free":
                continue  # Skip variant, use normalized version

            count = dietary_counts.get(flag, 0)
            percentage = count / total_items if total_items > 0 else 0

            if percentage >= DietaryAnalyzer.THRESHOLD:
                dietary_flags[flag] = True
            else:
                dietary_flags[flag] = False

        return dietary_flags
