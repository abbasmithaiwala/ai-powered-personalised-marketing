"""Campaign service for managing marketing campaigns"""

import logging
import random
from typing import List, Tuple, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload

from app.models import Campaign, CampaignRecipient, Customer
from app.schemas.campaign import (
    CampaignCreate,
    CampaignUpdate,
    SegmentFilters,
)
from app.schemas.message import MessageGenerationRequest
from app.services.segmentation_service import SegmentationService
from app.services.ai.message_generator import (
    MessageGenerator,
    MessageGenerationException,
    CustomerNotFoundError,
    InsufficientDataError,
)

logger = logging.getLogger(__name__)


class CampaignNotFoundError(Exception):
    """Raised when campaign is not found"""

    pass


class CampaignStateError(Exception):
    """Raised when campaign is in invalid state for operation"""

    pass


class CampaignService:
    """
    Service for campaign lifecycle management.

    Handles campaign creation, preview, execution, and monitoring.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.segmentation_service = SegmentationService(db)
        self.message_generator = MessageGenerator(db)

    async def create_campaign(self, campaign_data: CampaignCreate) -> Campaign:
        """
        Create a new campaign in draft status.

        Args:
            campaign_data: Campaign creation data

        Returns:
            Created campaign
        """
        # Convert segment_filters to dict if present
        segment_filters_dict = None
        if campaign_data.segment_filters:
            segment_filters_dict = campaign_data.segment_filters.model_dump(exclude_none=True)

        campaign = Campaign(
            name=campaign_data.name,
            description=campaign_data.description,
            purpose=campaign_data.purpose,
            segment_filters=segment_filters_dict,
            status="draft",
            total_recipients=0,
            generated_count=0,
        )

        self.db.add(campaign)
        await self.db.commit()
        await self.db.refresh(campaign)

        logger.info(f"Created campaign: {campaign.id} - {campaign.name}")
        return campaign

    async def get_campaign(self, campaign_id: UUID) -> Campaign:
        """
        Get campaign by ID.

        Args:
            campaign_id: Campaign ID

        Returns:
            Campaign

        Raises:
            CampaignNotFoundError: If campaign doesn't exist
        """
        result = await self.db.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )
        campaign = result.scalar_one_or_none()

        if not campaign:
            raise CampaignNotFoundError(f"Campaign {campaign_id} not found")

        return campaign

    async def list_campaigns(
        self, page: int = 1, page_size: int = 25
    ) -> Tuple[List[Campaign], int]:
        """
        List all campaigns with pagination.

        Args:
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (campaigns list, total count)
        """
        # Get total count
        count_result = await self.db.execute(select(func.count(Campaign.id)))
        total = count_result.scalar_one()

        # Get campaigns
        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(Campaign)
            .order_by(Campaign.created_at.desc())
            .limit(page_size)
            .offset(offset)
        )
        campaigns = list(result.scalars().all())

        return campaigns, total

    async def update_campaign(
        self, campaign_id: UUID, update_data: CampaignUpdate
    ) -> Campaign:
        """
        Update a draft campaign.

        Args:
            campaign_id: Campaign ID
            update_data: Fields to update

        Returns:
            Updated campaign

        Raises:
            CampaignNotFoundError: If campaign doesn't exist
            CampaignStateError: If campaign is not in draft status
        """
        campaign = await self.get_campaign(campaign_id)

        if campaign.status != "draft":
            raise CampaignStateError(
                f"Cannot update campaign in status '{campaign.status}'. "
                "Only draft campaigns can be updated."
            )

        # Update fields
        update_dict = update_data.model_dump(exclude_none=True)

        # Convert segment_filters to dict if present
        if "segment_filters" in update_dict:
            segment_filters = update_dict["segment_filters"]
            if segment_filters is not None:
                update_dict["segment_filters"] = segment_filters.model_dump(exclude_none=True)

        for field, value in update_dict.items():
            setattr(campaign, field, value)

        await self.db.commit()
        await self.db.refresh(campaign)

        logger.info(f"Updated campaign: {campaign_id}")
        return campaign

    async def preview_campaign(
        self, campaign_id: UUID, sample_size: int = 3, brand_group_name: str = "Our Restaurant Group"
    ) -> Tuple[Campaign, List[CampaignRecipient], int]:
        """
        Generate preview messages for a sample of customers.

        Args:
            campaign_id: Campaign ID
            sample_size: Number of preview messages to generate
            brand_group_name: Brand group name for message generation

        Returns:
            Tuple of (campaign, preview recipients, estimated audience size)

        Raises:
            CampaignNotFoundError: If campaign doesn't exist
        """
        campaign = await self.get_campaign(campaign_id)

        # Parse segment filters
        filters = self._parse_segment_filters(campaign.segment_filters)

        # Get audience count
        audience_size = await self.segmentation_service.count_segment(filters)

        if audience_size == 0:
            logger.warning(f"Campaign {campaign_id} has no matching customers")
            return campaign, [], 0

        # Get sample customers (request more to account for failures)
        sample_limit = min(sample_size * 3, audience_size)
        customers, _ = await self.segmentation_service.find_customers(
            filters, limit=sample_limit
        )

        # Randomly select sample_size customers
        sample_customers = random.sample(customers, min(sample_size, len(customers)))

        # Update campaign status
        campaign.status = "previewing"
        await self.db.commit()

        # Generate messages for sample
        preview_recipients = []
        from datetime import datetime, timezone
        import uuid
        for customer in sample_customers:
            recipient = await self._generate_message_for_customer(
                campaign, customer, brand_group_name
            )
            # Manually set fields for preview (not saved to DB)
            if recipient.id is None:
                recipient.id = uuid.uuid4()
            if recipient.created_at is None:
                recipient.created_at = datetime.now(timezone.utc)
            recipient.customer = customer
            preview_recipients.append(recipient)

        # Reset campaign status to draft after preview
        campaign.status = "draft"
        await self.db.commit()

        logger.info(
            f"Generated {len(preview_recipients)} preview messages for campaign {campaign_id}"
        )

        return campaign, preview_recipients, audience_size

    async def execute_campaign(
        self, campaign_id: UUID, brand_group_name: str = "Our Restaurant Group"
    ) -> Campaign:
        """
        Execute campaign by generating messages for all recipients.

        Args:
            campaign_id: Campaign ID
            brand_group_name: Brand group name for message generation

        Returns:
            Updated campaign

        Raises:
            CampaignNotFoundError: If campaign doesn't exist
            CampaignStateError: If campaign is not in draft status
        """
        campaign = await self.get_campaign(campaign_id)

        if campaign.status not in ("draft", "ready"):
            raise CampaignStateError(
                f"Cannot execute campaign in status '{campaign.status}'"
            )

        # Parse segment filters
        filters = self._parse_segment_filters(campaign.segment_filters)

        # Get all matching customers
        customers, total = await self.segmentation_service.find_customers(
            filters, limit=10000  # MVP limit
        )

        if total == 0:
            raise CampaignStateError("No customers match campaign filters")

        # Update campaign status and total recipients
        campaign.status = "executing"
        campaign.total_recipients = total
        campaign.generated_count = 0
        await self.db.commit()

        # Create recipient records
        recipients = []
        for customer in customers:
            recipient = CampaignRecipient(
                campaign_id=campaign.id,
                customer_id=customer.id,
                status="pending",
            )
            recipients.append(recipient)

        self.db.add_all(recipients)
        await self.db.commit()

        logger.info(
            f"Created {len(recipients)} recipient records for campaign {campaign_id}"
        )

        # Generate messages for each recipient
        success_count = 0
        fail_count = 0

        for recipient in recipients:
            try:
                # Fetch customer (with fresh session state)
                customer = await self.db.get(Customer, recipient.customer_id)

                # Generate message
                updated_recipient = await self._generate_message_for_customer(
                    campaign, customer, brand_group_name, recipient
                )

                if updated_recipient.status == "generated":
                    success_count += 1
                else:
                    fail_count += 1

                # Update campaign progress
                campaign.generated_count = success_count + fail_count
                await self.db.commit()

            except Exception as e:
                logger.error(
                    f"Failed to generate message for recipient {recipient.id}: {e}"
                )
                fail_count += 1
                continue

        # Update final campaign status
        campaign.status = "completed"
        await self.db.commit()
        await self.db.refresh(campaign)

        logger.info(
            f"Completed campaign {campaign_id}: "
            f"{success_count} generated, {fail_count} failed"
        )

        return campaign

    async def get_recipients(
        self, campaign_id: UUID, page: int = 1, page_size: int = 25
    ) -> Tuple[List[CampaignRecipient], int]:
        """
        Get campaign recipients with pagination.

        Args:
            campaign_id: Campaign ID
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (recipients list, total count)

        Raises:
            CampaignNotFoundError: If campaign doesn't exist
        """
        # Verify campaign exists
        await self.get_campaign(campaign_id)

        # Get total count
        count_result = await self.db.execute(
            select(func.count(CampaignRecipient.id)).where(
                CampaignRecipient.campaign_id == campaign_id
            )
        )
        total = count_result.scalar_one()

        # Get recipients
        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(CampaignRecipient)
            .where(CampaignRecipient.campaign_id == campaign_id)
            .options(selectinload(CampaignRecipient.customer))
            .order_by(CampaignRecipient.created_at.asc())
            .limit(page_size)
            .offset(offset)
        )
        recipients = list(result.scalars().all())

        return recipients, total

    async def _generate_message_for_customer(
        self,
        campaign: Campaign,
        customer: Customer,
        brand_group_name: str,
        recipient: Optional[CampaignRecipient] = None,
    ) -> CampaignRecipient:
        """
        Generate personalized message for a customer.

        Args:
            campaign: Campaign
            customer: Customer
            brand_group_name: Brand group name
            recipient: Existing recipient record (for execution), or None (for preview)

        Returns:
            Campaign recipient with generated message
        """
        try:
            # Build message generation request
            request = MessageGenerationRequest(
                customer_id=customer.id,
                campaign_purpose=campaign.purpose or campaign.description or campaign.name,
                brand_group_name=brand_group_name,
                offer=None,  # Can be extended later
                recommendation_limit=3,
            )

            # Generate message
            response = await self.message_generator.generate_message(request)

            # Prepare message data
            message_data = {
                "subject": response.message.subject,
                "body": response.message.body,
                "model_used": response.model_used,
                "recommendations": response.recommendations_used,
            }

            # Create or update recipient
            if recipient is None:
                # Preview mode - create temporary recipient (not saved)
                recipient = CampaignRecipient(
                    campaign_id=campaign.id,
                    customer_id=customer.id,
                    generated_message=message_data,
                    status="generated",
                )
            else:
                # Execution mode - update existing recipient
                recipient.generated_message = message_data
                recipient.status = "generated"
                await self.db.commit()
                await self.db.refresh(recipient)

            logger.debug(
                f"Generated message for customer {customer.id} in campaign {campaign.id}"
            )

            return recipient

        except (CustomerNotFoundError, InsufficientDataError) as e:
            error_msg = f"Cannot generate message: {str(e)}"
            logger.warning(error_msg)

            if recipient is None:
                recipient = CampaignRecipient(
                    campaign_id=campaign.id,
                    customer_id=customer.id,
                    status="failed",
                    error_message=error_msg,
                )
            else:
                recipient.status = "failed"
                recipient.error_message = error_msg
                await self.db.commit()
                await self.db.refresh(recipient)

            return recipient

        except MessageGenerationException as e:
            error_msg = f"Message generation failed: {str(e)}"
            logger.error(error_msg)

            if recipient is None:
                recipient = CampaignRecipient(
                    campaign_id=campaign.id,
                    customer_id=customer.id,
                    status="failed",
                    error_message=error_msg,
                )
            else:
                recipient.status = "failed"
                recipient.error_message = error_msg
                await self.db.commit()
                await self.db.refresh(recipient)

            return recipient

    def _parse_segment_filters(
        self, segment_filters_dict: Optional[dict]
    ) -> SegmentFilters:
        """
        Parse segment filters dict to SegmentFilters schema.

        Args:
            segment_filters_dict: Segment filters as dict (from JSON column)

        Returns:
            SegmentFilters schema
        """
        if segment_filters_dict is None:
            return SegmentFilters()

        return SegmentFilters(**segment_filters_dict)
