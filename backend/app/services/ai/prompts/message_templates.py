"""User prompt templates for message generation"""

from typing import List
from datetime import datetime


def build_user_prompt(
    first_name: str,
    last_order_summary: str,
    recommendations: List[str],
    campaign_purpose: str,
    offer: str | None = None,
) -> str:
    """
    Build the user prompt for message generation.

    Args:
        first_name: Customer's first name
        last_order_summary: Summary of their last order(s)
        recommendations: List of recommended dish names
        campaign_purpose: Purpose/theme of the campaign
        offer: Optional special offer or promotion

    Returns:
        Formatted user prompt string
    """
    recommendations_text = "\n".join(f"- {rec}" for rec in recommendations)

    prompt_parts = [
        f"Customer first name: {first_name}",
        f"\nLast order summary: {last_order_summary}",
        f"\nRecommended dishes:\n{recommendations_text}",
        f"\nCampaign purpose: {campaign_purpose}",
    ]

    if offer:
        prompt_parts.append(f"\nSpecial offer: {offer}")

    return "\n".join(prompt_parts)


def format_last_order_summary(
    last_order_date: datetime | None,
    last_order_items: List[str],
    days_since_order: int | None = None,
) -> str:
    """
    Format a summary of the customer's last order.

    Args:
        last_order_date: Date of last order
        last_order_items: List of item names from last order
        days_since_order: Optional number of days since last order

    Returns:
        Formatted summary string
    """
    if not last_order_date or not last_order_items:
        return "This customer hasn't ordered recently"

    items_text = ", ".join(last_order_items[:3])  # Show max 3 items
    if len(last_order_items) > 3:
        items_text += f" (and {len(last_order_items) - 3} more)"

    if days_since_order is not None:
        if days_since_order == 0:
            time_text = "today"
        elif days_since_order == 1:
            time_text = "yesterday"
        elif days_since_order < 7:
            time_text = f"{days_since_order} days ago"
        elif days_since_order < 30:
            weeks = days_since_order // 7
            time_text = f"{weeks} week{'s' if weeks > 1 else ''} ago"
        else:
            months = days_since_order // 30
            time_text = f"{months} month{'s' if months > 1 else ''} ago"

        return f"Ordered {time_text}: {items_text}"
    else:
        return f"Last order: {items_text}"
