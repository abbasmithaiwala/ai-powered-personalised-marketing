"""Integration tests for campaign API endpoints"""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from app.models import Campaign, Customer, CustomerPreference


@pytest.mark.asyncio
class TestCampaignAPI:
    """Test suite for campaign API endpoints"""

    async def test_create_campaign(self, async_client):
        """Test POST /campaigns to create new campaign"""
        response = await async_client.post(
            "/api/v1/campaigns",
            json={
                "name": "Spring Promotion",
                "description": "Promote spring menu items",
                "purpose": "Drive sales for seasonal dishes",
                "segment_filters": {
                    "total_orders_min": 5,
                    "favorite_cuisine": "italian"
                }
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Spring Promotion"
        assert data["status"] == "draft"
        assert data["total_recipients"] == 0
        assert "id" in data

    async def test_list_campaigns(self, async_client, db_session):
        """Test GET /campaigns to list all campaigns"""
        # Create a campaign
        campaign = Campaign(
            name="Test Campaign",
            status="draft",
        )
        db_session.add(campaign)
        await db_session.commit()

        response = await async_client.get("/api/v1/campaigns")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    async def test_get_campaign(self, async_client, db_session):
        """Test GET /campaigns/{id} to get campaign details"""
        campaign = Campaign(
            name="Test Campaign",
            description="Test",
            status="draft",
        )
        db_session.add(campaign)
        await db_session.commit()

        response = await async_client.get(f"/api/v1/campaigns/{campaign.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(campaign.id)
        assert data["name"] == "Test Campaign"

    async def test_get_campaign_not_found(self, async_client):
        """Test GET /campaigns/{id} with non-existent ID"""
        from uuid import uuid4
        response = await async_client.get(f"/api/v1/campaigns/{uuid4()}")

        assert response.status_code == 404

    async def test_update_campaign(self, async_client, db_session):
        """Test PUT /campaigns/{id} to update draft campaign"""
        campaign = Campaign(
            name="Original Name",
            status="draft",
        )
        db_session.add(campaign)
        await db_session.commit()

        response = await async_client.put(
            f"/api/v1/campaigns/{campaign.id}",
            json={
                "name": "Updated Name",
                "description": "New description"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "New description"

    async def test_update_completed_campaign_fails(self, async_client, db_session):
        """Test updating completed campaign returns error"""
        campaign = Campaign(
            name="Completed Campaign",
            status="completed",
        )
        db_session.add(campaign)
        await db_session.commit()

        response = await async_client.put(
            f"/api/v1/campaigns/{campaign.id}",
            json={"name": "New Name"}
        )

        assert response.status_code == 400
        assert "draft" in response.json()["detail"].lower()

    async def test_preview_campaign(self, async_client, db_session):
        """Test POST /campaigns/{id}/preview to generate sample messages"""
        # Create campaign
        campaign = Campaign(
            name="Test Campaign",
            purpose="Test preview",
            status="draft",
            segment_filters={"total_orders_min": 1},
        )
        db_session.add(campaign)
        await db_session.commit()

        # Create sample customers
        customers = [
            Customer(
                external_id=f"c{i}",
                email=f"c{i}@test.com",
                first_name=f"Customer{i}",
                total_orders=5,
                total_spend=Decimal("5000.0"),
            )
            for i in range(3)
        ]
        db_session.add_all(customers)
        await db_session.commit()

        # Add preferences
        for customer in customers:
            pref = CustomerPreference(
                customer_id=customer.id,
                favorite_cuisines={"italian": 0.8},
                order_frequency="weekly",
                last_computed_at=datetime.now(timezone.utc),
            )
            db_session.add(pref)
        await db_session.commit()

        # Mock message generation
        with patch('app.services.campaign_service.MessageGenerator') as mock_gen_class:
            mock_gen = AsyncMock()
            mock_gen_class.return_value = mock_gen

            from app.schemas.message import MessageGenerationResponse, GeneratedMessage
            mock_gen.generate_message.return_value = MessageGenerationResponse(
                customer_id=customers[0].id,
                message=GeneratedMessage(
                    subject="Test Subject",
                    body="Test Body"
                ),
                recommendations_used=["Item 1"],
                model_used="test-model",
            )

            response = await async_client.post(
                f"/api/v1/campaigns/{campaign.id}/preview",
                json={"sample_size": 2}
            )

            if response.status_code != 200:
                print(f"Error response: {response.json()}")
            assert response.status_code == 200
            data = response.json()
            assert data["campaign_id"] == str(campaign.id)
            assert data["estimated_audience_size"] == 3
            assert len(data["sample_messages"]) <= 2
            assert all("generated_message" in msg for msg in data["sample_messages"])

    async def test_execute_campaign(self, async_client, db_session):
        """Test POST /campaigns/{id}/execute to execute campaign"""
        # Create campaign
        campaign = Campaign(
            name="Test Campaign",
            purpose="Test execution",
            status="draft",
            segment_filters={"total_orders_min": 1},
        )
        db_session.add(campaign)
        await db_session.commit()

        # Create customers
        customers = [
            Customer(
                external_id=f"c{i}",
                email=f"c{i}@test.com",
                first_name=f"Customer{i}",
                total_orders=5,
                total_spend=Decimal("5000.0"),
            )
            for i in range(2)
        ]
        db_session.add_all(customers)
        await db_session.commit()

        # Add preferences
        for customer in customers:
            pref = CustomerPreference(
                customer_id=customer.id,
                favorite_cuisines={"italian": 0.8},
                order_frequency="weekly",
                last_computed_at=datetime.now(timezone.utc),
            )
            db_session.add(pref)
        await db_session.commit()

        # Mock message generation
        with patch('app.services.campaign_service.MessageGenerator') as mock_gen_class:
            mock_gen = AsyncMock()
            mock_gen_class.return_value = mock_gen

            from app.schemas.message import MessageGenerationResponse, GeneratedMessage
            mock_gen.generate_message.return_value = MessageGenerationResponse(
                customer_id=customers[0].id,
                message=GeneratedMessage(
                    subject="Test Subject",
                    body="Test Body"
                ),
                recommendations_used=["Item 1"],
                model_used="test-model",
            )

            response = await async_client.post(
                f"/api/v1/campaigns/{campaign.id}/execute"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["campaign_id"] == str(campaign.id)
            assert data["status"] == "completed"
            assert data["total_recipients"] == 2

    async def test_execute_campaign_no_customers(self, async_client, db_session):
        """Test executing campaign with no matching customers"""
        campaign = Campaign(
            name="Test Campaign",
            status="draft",
            segment_filters={"total_orders_min": 1000},  # No one has this many
        )
        db_session.add(campaign)
        await db_session.commit()

        response = await async_client.post(
            f"/api/v1/campaigns/{campaign.id}/execute"
        )

        assert response.status_code == 400
        assert "no customers" in response.json()["detail"].lower()

    async def test_get_recipients(self, async_client, db_session):
        """Test GET /campaigns/{id}/recipients to list recipients"""
        from app.models import CampaignRecipient

        # Create campaign
        campaign = Campaign(
            name="Test Campaign",
            status="completed",
            total_recipients=2,
        )
        db_session.add(campaign)
        await db_session.commit()

        # Create customer and recipients
        customer1 = Customer(
            external_id="c1",
            email="c1@test.com",
            first_name="John",
            total_orders=5,
            total_spend=Decimal("5000.0"),
        )
        customer2 = Customer(
            external_id="c2",
            email="c2@test.com",
            first_name="Jane",
            total_orders=3,
            total_spend=Decimal("3000.0"),
        )
        db_session.add_all([customer1, customer2])
        await db_session.commit()

        recipient1 = CampaignRecipient(
            campaign_id=campaign.id,
            customer_id=customer1.id,
            status="generated",
            generated_message={
                "subject": "Hi John!",
                "body": "Check out our new dishes..."
            }
        )
        recipient2 = CampaignRecipient(
            campaign_id=campaign.id,
            customer_id=customer2.id,
            status="generated",
            generated_message={
                "subject": "Hi Jane!",
                "body": "We have great offers..."
            }
        )
        db_session.add_all([recipient1, recipient2])
        await db_session.commit()

        response = await async_client.get(
            f"/api/v1/campaigns/{campaign.id}/recipients"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert all("customer_email" in item for item in data["items"])
        assert all("generated_message" in item for item in data["items"])

    async def test_segment_count(self, async_client, db_session):
        """Test POST /campaigns/segment-count to count audience"""
        # Create customers
        customers = [
            Customer(
                external_id=f"c{i}",
                email=f"c{i}@test.com",
                total_orders=i * 2,
                total_spend=Decimal(str(i * 1000)),
            )
            for i in range(1, 6)
        ]
        db_session.add_all(customers)
        await db_session.commit()

        response = await async_client.post(
            "/api/v1/campaigns/segment-count",
            json={
                "filters": {
                    "total_orders_min": 4
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        # Customers with 4+ orders: c2(4), c3(6), c4(8), c5(10) = 4 customers
        assert data["count"] >= 3

    async def test_pagination(self, async_client, db_session):
        """Test campaign list pagination"""
        # Create multiple campaigns
        campaigns = [
            Campaign(name=f"Campaign {i}", status="draft")
            for i in range(10)
        ]
        db_session.add_all(campaigns)
        await db_session.commit()

        # First page
        response = await async_client.get("/api/v1/campaigns?page=1&page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert data["total"] >= 10

        # Second page
        response = await async_client.get("/api/v1/campaigns?page=2&page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 5
        assert data["page"] == 2
