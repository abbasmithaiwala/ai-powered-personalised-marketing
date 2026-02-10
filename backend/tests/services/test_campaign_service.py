"""Tests for campaign service"""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from app.services.campaign_service import (
    CampaignService,
    CampaignNotFoundError,
    CampaignStateError,
)
from app.schemas.campaign import CampaignCreate, CampaignUpdate, SegmentFilters
from app.models import Customer, Campaign, CampaignRecipient


@pytest.mark.asyncio
class TestCampaignService:
    """Test suite for CampaignService"""

    async def test_create_campaign(self, db_session):
        """Test creating a new campaign"""
        service = CampaignService(db_session)

        campaign_data = CampaignCreate(
            name="Test Campaign",
            description="A test marketing campaign",
            purpose="Promote new menu items",
            segment_filters=SegmentFilters(total_orders_min=5),
        )

        campaign = await service.create_campaign(campaign_data)

        assert campaign.id is not None
        assert campaign.name == "Test Campaign"
        assert campaign.description == "A test marketing campaign"
        assert campaign.purpose == "Promote new menu items"
        assert campaign.status == "draft"
        assert campaign.total_recipients == 0
        assert campaign.generated_count == 0
        assert campaign.segment_filters is not None

    async def test_get_campaign(self, db_session, sample_campaign):
        """Test getting campaign by ID"""
        service = CampaignService(db_session)

        campaign = await service.get_campaign(sample_campaign.id)

        assert campaign.id == sample_campaign.id
        assert campaign.name == sample_campaign.name

    async def test_get_campaign_not_found(self, db_session):
        """Test getting non-existent campaign raises error"""
        service = CampaignService(db_session)

        from uuid import uuid4
        with pytest.raises(CampaignNotFoundError):
            await service.get_campaign(uuid4())

    async def test_list_campaigns(self, db_session, sample_campaign):
        """Test listing campaigns with pagination"""
        service = CampaignService(db_session)

        campaigns, total = await service.list_campaigns(page=1, page_size=10)

        assert total >= 1
        assert len(campaigns) >= 1
        assert any(c.id == sample_campaign.id for c in campaigns)

    async def test_update_campaign(self, db_session, sample_campaign):
        """Test updating a draft campaign"""
        service = CampaignService(db_session)

        update_data = CampaignUpdate(
            name="Updated Name",
            description="Updated description",
        )

        updated = await service.update_campaign(sample_campaign.id, update_data)

        assert updated.name == "Updated Name"
        assert updated.description == "Updated description"
        assert updated.purpose == sample_campaign.purpose  # Unchanged

    async def test_update_campaign_not_draft(self, db_session, sample_campaign):
        """Test updating non-draft campaign raises error"""
        service = CampaignService(db_session)

        # Change status to completed
        sample_campaign.status = "completed"
        await db_session.commit()

        update_data = CampaignUpdate(name="New Name")

        with pytest.raises(CampaignStateError):
            await service.update_campaign(sample_campaign.id, update_data)

    async def test_preview_campaign_no_customers(self, db_session, sample_campaign):
        """Test preview with no matching customers"""
        service = CampaignService(db_session)

        campaign, recipients, audience_size = await service.preview_campaign(
            sample_campaign.id,
            sample_size=3,
        )

        assert audience_size == 0
        assert len(recipients) == 0
        assert campaign.status == "draft"  # Should reset to draft after preview

    async def test_preview_campaign_with_customers(
        self, db_session, sample_campaign, sample_customers_with_preferences
    ):
        """Test preview generates messages for sample customers"""
        service = CampaignService(db_session)

        # Mock message generation
        with patch.object(
            service.message_generator,
            'generate_message',
            new_callable=AsyncMock
        ) as mock_generate:
            # Mock successful message generation
            from app.schemas.message import MessageGenerationResponse, GeneratedMessage
            mock_generate.return_value = MessageGenerationResponse(
                customer_id=sample_customers_with_preferences[0].id,
                message=GeneratedMessage(
                    subject="Try our new Italian dishes!",
                    body="Hi there! We have amazing new pasta dishes..."
                ),
                recommendations_used=["Pasta Carbonara", "Tiramisu"],
                model_used="test-model",
            )

            campaign, recipients, audience_size = await service.preview_campaign(
                sample_campaign.id,
                sample_size=2,
            )

            assert audience_size == len(sample_customers_with_preferences)
            assert len(recipients) <= 2
            assert all(r.status == "generated" for r in recipients)
            assert all(r.generated_message is not None for r in recipients)

    async def test_execute_campaign_draft_status(
        self, db_session, sample_campaign, sample_customers_with_preferences
    ):
        """Test executing a draft campaign"""
        service = CampaignService(db_session)

        # Mock message generation
        with patch.object(
            service.message_generator,
            'generate_message',
            new_callable=AsyncMock
        ) as mock_generate:
            from app.schemas.message import MessageGenerationResponse, GeneratedMessage
            mock_generate.return_value = MessageGenerationResponse(
                customer_id=sample_customers_with_preferences[0].id,
                message=GeneratedMessage(
                    subject="Test Subject",
                    body="Test Body"
                ),
                recommendations_used=["Item 1"],
                model_used="test-model",
            )

            campaign = await service.execute_campaign(sample_campaign.id)

            assert campaign.status == "completed"
            assert campaign.total_recipients == len(sample_customers_with_preferences)
            assert campaign.generated_count > 0

    async def test_execute_campaign_invalid_status(self, db_session, sample_campaign):
        """Test executing campaign in invalid status raises error"""
        service = CampaignService(db_session)

        # Change status to completed
        sample_campaign.status = "completed"
        await db_session.commit()

        with pytest.raises(CampaignStateError):
            await service.execute_campaign(sample_campaign.id)

    async def test_execute_campaign_no_customers(self, db_session, sample_campaign):
        """Test executing campaign with no matching customers raises error"""
        service = CampaignService(db_session)

        with pytest.raises(CampaignStateError, match="No customers match"):
            await service.execute_campaign(sample_campaign.id)

    async def test_get_recipients(self, db_session, sample_campaign):
        """Test getting campaign recipients with pagination"""
        service = CampaignService(db_session)

        # Create some recipients
        from app.models import Customer
        customer = Customer(
            external_id="test",
            email="test@test.com",
            total_orders=1,
            total_spend=Decimal("10.0"),
        )
        db_session.add(customer)
        await db_session.commit()

        recipient = CampaignRecipient(
            campaign_id=sample_campaign.id,
            customer_id=customer.id,
            status="pending",
        )
        db_session.add(recipient)
        await db_session.commit()

        recipients, total = await service.get_recipients(
            sample_campaign.id,
            page=1,
            page_size=10,
        )

        assert total >= 1
        assert len(recipients) >= 1
        assert recipients[0].campaign_id == sample_campaign.id

    async def test_message_generation_failure_handling(
        self, db_session, sample_campaign, sample_customers_with_preferences
    ):
        """Test that message generation failures are captured per-recipient"""
        service = CampaignService(db_session)

        # Mock message generation to fail
        with patch.object(
            service.message_generator,
            'generate_message',
            new_callable=AsyncMock
        ) as mock_generate:
            from app.services.ai.message_generator import InsufficientDataError
            mock_generate.side_effect = InsufficientDataError("No recommendations")

            campaign = await service.execute_campaign(sample_campaign.id)

            # Campaign should complete even with failures
            assert campaign.status == "completed"
            assert campaign.total_recipients == len(sample_customers_with_preferences)

            # Check that recipients have failed status
            recipients, _ = await service.get_recipients(campaign.id, page=1, page_size=100)
            assert all(r.status == "failed" for r in recipients)
            assert all(r.error_message is not None for r in recipients)


@pytest.fixture
async def sample_campaign(db_session):
    """Create a sample campaign for testing"""
    campaign = Campaign(
        name="Test Campaign",
        description="Test Description",
        purpose="Test Purpose",
        status="draft",
        segment_filters={
            "total_orders_min": 1
        },
    )
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)
    return campaign


@pytest.fixture
async def sample_customers_with_preferences(db_session):
    """Create sample customers with preferences for testing"""
    from app.models import CustomerPreference

    customers = [
        Customer(
            external_id=f"c{i}",
            email=f"c{i}@test.com",
            first_name=f"Customer{i}",
            total_orders=5,
            total_spend=Decimal("50.0"),
            last_order_at=datetime.now(timezone.utc) - timedelta(days=10),
        )
        for i in range(3)
    ]
    db_session.add_all(customers)
    await db_session.commit()

    # Add preferences for each customer
    for customer in customers:
        preference = CustomerPreference(
            customer_id=customer.id,
            favorite_cuisines={"italian": 0.8},
            dietary_flags={},
            order_frequency="weekly",
            last_computed_at=datetime.now(timezone.utc),
        )
        db_session.add(preference)

    await db_session.commit()
    return customers
