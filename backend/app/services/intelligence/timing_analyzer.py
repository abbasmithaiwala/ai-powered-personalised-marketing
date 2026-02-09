"""Order timing pattern analyzer"""

from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Literal


OrderFrequency = Literal["daily", "weekly", "monthly", "occasional"]


class TimingAnalyzer:
    """Analyze customer order timing patterns"""

    # Order frequency thresholds (orders per month)
    DAILY_THRESHOLD = 20
    WEEKLY_THRESHOLD = 4
    MONTHLY_THRESHOLD = 1

    # Time bins (hour ranges)
    TIME_BINS = {
        "breakfast": (6, 11),
        "lunch": (11, 15),
        "dinner": (17, 22),
        "late_night": (22, 6),  # Special handling for wraparound
    }

    @staticmethod
    def compute_order_frequency(order_dates: List[datetime]) -> OrderFrequency:
        """
        Compute order frequency based on order history.

        Args:
            order_dates: List of order timestamps

        Returns:
            "daily" (>20/month), "weekly" (4-20/month), "monthly" (1-4/month), "occasional" (<1/month)
        """
        if not order_dates:
            return "occasional"

        # Find the span of order history
        min_date = min(order_dates)
        max_date = max(order_dates)

        # Calculate months of history
        days_span = (max_date - min_date).days
        months_span = max(days_span / 30.0, 1.0)  # At least 1 month

        # Calculate orders per month
        orders_per_month = len(order_dates) / months_span

        if orders_per_month > TimingAnalyzer.DAILY_THRESHOLD:
            return "daily"
        elif orders_per_month >= TimingAnalyzer.WEEKLY_THRESHOLD:
            return "weekly"
        elif orders_per_month >= TimingAnalyzer.MONTHLY_THRESHOLD:
            return "monthly"
        else:
            return "occasional"

    @staticmethod
    def compute_preferred_order_times(order_dates: List[datetime]) -> Dict[str, float]:
        """
        Analyze preferred order times by binning into meal periods.

        Args:
            order_dates: List of order timestamps

        Returns:
            Dict of time_period -> normalized score (0-1)
        """
        if not order_dates:
            return {}

        # Count orders in each time bin
        bin_counts = defaultdict(int)

        for order_date in order_dates:
            hour = order_date.hour

            # Determine which bin this hour falls into
            if TimingAnalyzer.TIME_BINS["breakfast"][0] <= hour < TimingAnalyzer.TIME_BINS["breakfast"][1]:
                bin_counts["breakfast"] += 1
            elif TimingAnalyzer.TIME_BINS["lunch"][0] <= hour < TimingAnalyzer.TIME_BINS["lunch"][1]:
                bin_counts["lunch"] += 1
            elif TimingAnalyzer.TIME_BINS["dinner"][0] <= hour < TimingAnalyzer.TIME_BINS["dinner"][1]:
                bin_counts["dinner"] += 1
            else:
                # Late night: 22-24 or 0-6
                bin_counts["late_night"] += 1

        # Normalize to 0-1 range
        total_orders = len(order_dates)
        normalized_times = {
            bin_name: count / total_orders
            for bin_name, count in bin_counts.items()
        }

        return normalized_times
