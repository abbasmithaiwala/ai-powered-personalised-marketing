"""Campaign API endpoints"""

import math
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.campaign_service import (
    CampaignService,
    CampaignNotFoundError,
    CampaignStateError,
)
from app.services.ai.openrouter_client import (
    OpenRouterAPIKeyError,
    OpenRouterError,
)
from app.services.ai.groq_client import (
    GroqAPIKeyError,
    GroqError,
)
from app.services.segmentation_service import SegmentationService
from app.schemas.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignListResponse,
    CampaignPreviewRequest,
    CampaignPreviewResponse,
    CampaignExecuteResponse,
    CampaignRecipientResponse,
    CampaignRecipientListResponse,
    AudienceCountRequest,
    AudienceCountResponse,
)

router = APIRouter()


@router.get("", response_model=CampaignListResponse)
async def list_campaigns(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """
    List all campaigns with pagination.

    Returns campaigns ordered by creation date (most recent first).
    """
    service = CampaignService(db)
    campaigns, total = await service.list_campaigns(page=page, page_size=page_size)

    pages = math.ceil(total / page_size) if total > 0 else 0

    return CampaignListResponse(
        items=[CampaignResponse.model_validate(c) for c in campaigns],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post("", response_model=CampaignResponse, status_code=201)
async def create_campaign(
    campaign_data: CampaignCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new campaign in draft status.

    The campaign is created with status 'draft' and can be edited before execution.
    """
    service = CampaignService(db)
    campaign = await service.create_campaign(campaign_data)
    return CampaignResponse.model_validate(campaign)


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get campaign details by ID.

    Returns full campaign details including progress metrics.
    """
    try:
        service = CampaignService(db)
        campaign = await service.get_campaign(campaign_id)
        return CampaignResponse.model_validate(campaign)
    except CampaignNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: UUID,
    update_data: CampaignUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a draft campaign.

    Only campaigns in 'draft' status can be updated. Completed campaigns are immutable.
    """
    try:
        service = CampaignService(db)
        campaign = await service.update_campaign(campaign_id, update_data)
        return CampaignResponse.model_validate(campaign)
    except CampaignNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CampaignStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{campaign_id}/preview", response_model=CampaignPreviewResponse)
async def preview_campaign(
    campaign_id: UUID,
    preview_request: CampaignPreviewRequest = CampaignPreviewRequest(),
    brand_group_name: str = Query(
        "Our Restaurant Group",
        description="Brand group name for message personalization",
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate preview messages for a sample of customers.

    This generates AI-powered personalized messages for a small sample (default 3)
    of customers matching the campaign's segment filters. Use this to verify
    message quality before executing the full campaign.

    Returns sample messages and the estimated total audience size.
    """
    try:
        service = CampaignService(db)
        campaign, recipients, audience_size = await service.preview_campaign(
            campaign_id=campaign_id,
            sample_size=preview_request.sample_size,
            brand_group_name=brand_group_name,
            llm_provider=preview_request.llm_provider,
            llm_model=preview_request.llm_model,
        )

        # Convert recipients to response format
        recipient_responses = []
        for recipient in recipients:
            response = CampaignRecipientResponse.model_validate(recipient)
            # Add customer info
            if recipient.customer:
                response.customer_email = recipient.customer.email
                customer_name = None
                if recipient.customer.first_name:
                    customer_name = recipient.customer.first_name
                    if recipient.customer.last_name:
                        customer_name += f" {recipient.customer.last_name}"
                response.customer_name = customer_name
            recipient_responses.append(response)

        return CampaignPreviewResponse(
            campaign_id=campaign.id,
            sample_messages=recipient_responses,
            estimated_audience_size=audience_size,
        )

    except CampaignNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (OpenRouterAPIKeyError, GroqAPIKeyError) as e:
        raise HTTPException(
            status_code=503,
            detail=f"{str(e)}. Please check your environment variables.",
        )
    except (OpenRouterError, GroqError) as e:
        raise HTTPException(
            status_code=503, detail=f"AI service temporarily unavailable: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate preview: {str(e)}"
        )


@router.post("/{campaign_id}/execute", response_model=CampaignExecuteResponse)
async def execute_campaign(
    campaign_id: UUID,
    brand_group_name: str = Query(
        "Our Restaurant Group",
        description="Brand group name for message personalization",
    ),
    llm_provider: str = Query(
        "openrouter",
        description="LLM provider to use (openrouter | groq)",
    ),
    llm_model: str = Query(
        None,
        description="Specific model to use",
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute campaign by generating messages for all recipients.

    This starts the campaign execution process:
    1. Identifies all customers matching the campaign's segment filters
    2. Creates recipient records for each customer
    3. Generates personalized AI messages for each recipient
    4. Updates campaign status to 'completed' when done

    For MVP, this runs synchronously. For large campaigns (>500 recipients),
    consider using async job processing in production.

    Poll GET /campaigns/{id} to track progress via generated_count / total_recipients.
    """
    try:
        service = CampaignService(db)
        campaign = await service.execute_campaign(
            campaign_id=campaign_id,
            brand_group_name=brand_group_name,
            llm_provider=llm_provider,
            llm_model=llm_model,
        )

        return CampaignExecuteResponse(
            campaign_id=campaign.id,
            status=campaign.status,
            total_recipients=campaign.total_recipients,
            message=f"Campaign execution completed. Generated {campaign.generated_count} messages.",
        )

    except CampaignNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CampaignStateError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (OpenRouterAPIKeyError, GroqAPIKeyError) as e:
        raise HTTPException(
            status_code=503,
            detail=f"{str(e)}. Please check your environment variables.",
        )
    except (OpenRouterError, GroqError) as e:
        raise HTTPException(
            status_code=503, detail=f"AI service temporarily unavailable: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to execute campaign: {str(e)}"
        )


@router.get("/{campaign_id}/recipients", response_model=CampaignRecipientListResponse)
async def get_campaign_recipients(
    campaign_id: UUID,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get campaign recipients with their generated messages.

    Returns paginated list of all recipients in the campaign, including:
    - Customer information
    - Generated message (subject + body)
    - Status (pending | generated | failed)
    - Error message (if failed)
    """
    try:
        service = CampaignService(db)
        recipients, total = await service.get_recipients(
            campaign_id=campaign_id,
            page=page,
            page_size=page_size,
        )

        pages = math.ceil(total / page_size) if total > 0 else 0

        # Convert recipients to response format
        recipient_responses = []
        for recipient in recipients:
            response = CampaignRecipientResponse.model_validate(recipient)
            # Add customer info
            if recipient.customer:
                response.customer_email = recipient.customer.email
                customer_name = None
                if recipient.customer.first_name:
                    customer_name = recipient.customer.first_name
                    if recipient.customer.last_name:
                        customer_name += f" {recipient.customer.last_name}"
                response.customer_name = customer_name
            recipient_responses.append(response)

        return CampaignRecipientListResponse(
            items=recipient_responses,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    except CampaignNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/segment-count", response_model=AudienceCountResponse)
async def get_segment_count(
    request: AudienceCountRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Count customers matching segment filters.

    Used for preview of campaign audience size before creation/execution.
    Returns the count quickly (<200ms) for UI responsiveness.
    """
    try:
        service = SegmentationService(db)
        count = await service.count_segment(request.filters)

        return AudienceCountResponse(
            count=count,
            filters=request.filters,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to count segment: {str(e)}"
        )
