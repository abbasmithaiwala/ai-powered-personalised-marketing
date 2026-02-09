"""
Manual test script for preference computation engine.

This script tests the full preference computation flow using the database.
Run this after ingesting some test data.

Usage:
    python test_preference_manual.py <customer_email>
"""

import asyncio
import sys
from uuid import UUID

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.customer import Customer
from app.services.intelligence import PreferenceEngine


async def test_preference_computation(customer_email: str):
    """Test preference computation for a customer"""
    async with AsyncSessionLocal() as db:
        # Find customer by email
        result = await db.execute(
            select(Customer).where(Customer.email == customer_email)
        )
        customer = result.scalar_one_or_none()

        if not customer:
            print(f"❌ Customer not found: {customer_email}")
            return

        print(f"✓ Found customer: {customer.email}")
        print(f"  - Total orders: {customer.total_orders}")
        print(f"  - Total spend: £{customer.total_spend}")
        print()

        # Compute preferences
        print("Computing preferences...")
        engine = PreferenceEngine(db)
        preference = await engine.compute_preferences(customer.id)

        print("\n✓ Preferences computed successfully!")
        print(f"\n📊 Customer Preference Profile:")
        print(f"Version: {preference.version}")
        print(f"Last computed: {preference.last_computed_at}")
        print()

        # Display results
        if preference.favorite_cuisines:
            print("🍽️  Favorite Cuisines:")
            for cuisine, score in sorted(
                preference.favorite_cuisines.items(),
                key=lambda x: x[1],
                reverse=True
            ):
                print(f"   - {cuisine.title()}: {score:.2f}")
            print()

        if preference.favorite_categories:
            print("📂 Favorite Categories:")
            for category, score in sorted(
                preference.favorite_categories.items(),
                key=lambda x: x[1],
                reverse=True
            ):
                print(f"   - {category.title()}: {score:.2f}")
            print()

        if preference.dietary_flags:
            active_flags = [
                flag for flag, active in preference.dietary_flags.items()
                if active
            ]
            if active_flags:
                print("🥗 Dietary Flags:")
                for flag in active_flags:
                    print(f"   - {flag.replace('_', ' ').title()}")
                print()

        print(f"💰 Price Sensitivity: {preference.price_sensitivity.upper()}")
        print(f"📅 Order Frequency: {preference.order_frequency.upper()}")
        print()

        if preference.preferred_order_times:
            print("⏰ Preferred Order Times:")
            for time_period, score in sorted(
                preference.preferred_order_times.items(),
                key=lambda x: x[1],
                reverse=True
            ):
                print(f"   - {time_period.replace('_', ' ').title()}: {score:.0%}")
            print()

        if preference.brand_affinity:
            print("🏪 Brand Affinity:")
            for brand in preference.brand_affinity[:5]:
                print(f"   - {brand['brand_name']}: {brand['score']:.2f}")
            print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_preference_manual.py <customer_email>")
        sys.exit(1)

    customer_email = sys.argv[1]
    asyncio.run(test_preference_computation(customer_email))
