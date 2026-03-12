"""Price sensitivity analyzer"""

from typing import List, Literal


PriceSensitivity = Literal["low", "medium", "high"]


class PriceAnalyzer:
    """Analyze customer price sensitivity from spending patterns"""

    # Thresholds in INR (configurable)
    LOW_THRESHOLD = 500.0
    HIGH_THRESHOLD = 2000.0

    @staticmethod
    def analyze(order_totals: List[float]) -> PriceSensitivity:
        """
        Compute price sensitivity based on average order value.

        Args:
            order_totals: List of order total amounts

        Returns:
            "low" (<₹500), "medium" (₹500-2000), or "high" (>₹2000)
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
            low: Lower threshold (e.g., 500.0 for ₹500)
            high: Upper threshold (e.g., 2000.0 for ₹2000)
        """
        PriceAnalyzer.LOW_THRESHOLD = low
        PriceAnalyzer.HIGH_THRESHOLD = high
