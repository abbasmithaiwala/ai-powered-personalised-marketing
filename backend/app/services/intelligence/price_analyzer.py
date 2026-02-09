"""Price sensitivity analyzer"""

from typing import List, Literal


PriceSensitivity = Literal["low", "medium", "high"]


class PriceAnalyzer:
    """Analyze customer price sensitivity from spending patterns"""

    # Thresholds in GBP (configurable)
    LOW_THRESHOLD = 10.0
    HIGH_THRESHOLD = 25.0

    @staticmethod
    def analyze(order_totals: List[float]) -> PriceSensitivity:
        """
        Compute price sensitivity based on average order value.

        Args:
            order_totals: List of order total amounts

        Returns:
            "low" (<£10), "medium" (£10-25), or "high" (>£25)
        """
        if not order_totals:
            return "medium"  # Default

        # Calculate average order value
        avg_order_value = sum(order_totals) / len(order_totals)

        if avg_order_value < PriceAnalyzer.LOW_THRESHOLD:
            return "low"
        elif avg_order_value <= PriceAnalyzer.HIGH_THRESHOLD:
            return "medium"
        else:
            return "high"

    @staticmethod
    def set_thresholds(low: float, high: float) -> None:
        """
        Update price thresholds (useful for different markets/currencies).

        Args:
            low: Lower threshold (e.g., 10.0 for £10)
            high: Upper threshold (e.g., 25.0 for £25)
        """
        PriceAnalyzer.LOW_THRESHOLD = low
        PriceAnalyzer.HIGH_THRESHOLD = high
