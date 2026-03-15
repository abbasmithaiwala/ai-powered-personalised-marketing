"""Personalized marketing message generator using LLM"""

import json
import logging
from uuid import UUID
from datetime import datetime, timezone
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Customer, Order, OrderItem
from app.services.ai.openrouter_client import (
    OpenRouterClient,
    OpenRouterError,
    OpenRouterAPIKeyError,
)
from app.services.ai.groq_client import (
    GroqClient,
    GroqError,
    GroqAPIKeyError,
)
from app.services.intelligence import RecommendationEngine
from app.services.ai.prompts import (
    MARKETING_MESSAGE_SYSTEM_PROMPT,
    build_user_prompt,
    format_last_order_summary,
)
from app.schemas.message import (
    GeneratedMessage,
    MessageGenerationRequest,
    MessageGenerationResponse,
    MessageGenerationError,
)
from app.schemas.recommendation import RecommendationItem

logger = logging.getLogger(__name__)


class MessageGenerationException(Exception):
    """Base exception for message generation errors"""

    pass


class CustomerNotFoundError(MessageGenerationException):
    """Raised when customer doesn't exist"""

    pass


class InsufficientDataError(MessageGenerationException):
    """Raised when customer has insufficient data for message generation"""

    pass


class MessageGenerator:
    """
    Service for generating personalized marketing messages using LLM.

    This service orchestrates:
    1. Fetching customer data and order history
    2. Getting personalized recommendations
    3. Building prompts with customer context
    4. Calling LLM to generate messages
    5. Validating and returning structured messages
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.recommendation_engine = RecommendationEngine(db)

    async def generate_message(
        self, request: MessageGenerationRequest
    ) -> MessageGenerationResponse:
        """
        Generate a personalized marketing message for a customer.

        Args:
            request: Message generation request with customer ID and campaign details

        Returns:
            MessageGenerationResponse with generated message and metadata

        Raises:
            CustomerNotFoundError: If customer doesn't exist
            InsufficientDataError: If customer has no order history
            OpenRouterAPIKeyError: If API key is not configured
            OpenRouterError: If LLM API call fails
            MessageGenerationException: For other generation errors
        """
        # 1. Fetch customer
        customer = await self._get_customer(request.customer_id)

        # 2. Get recommendations
        recommendations = await self._get_recommendations(
            request.customer_id, request.recommendation_limit
        )

        # 3. Get last order summary
        last_order_summary = await self._get_last_order_summary(request.customer_id)

        # 4. Build prompts
        system_prompt = MARKETING_MESSAGE_SYSTEM_PROMPT.format(
            brand_group_name=request.brand_group_name
        )

        user_prompt = build_user_prompt(
            first_name=customer.first_name or "there",
            last_order_summary=last_order_summary,
            recommendations=[rec.name for rec in recommendations],
            campaign_purpose=request.campaign_purpose,
            offer=request.offer,
        )

        # 5. Call LLM
        try:
            if request.llm_provider == "groq":
                async with GroqClient(model=request.llm_model) as client:
                    response_text = await client.complete(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=0.7,
                        max_tokens=256,
                        response_format={"type": "json_object"},
                    )
                    model_used = client.model
            else:
                # Default to OpenRouter
                async with OpenRouterClient(model=request.llm_model) as client:
                    response_text = await client.complete(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=0.7,
                        max_tokens=256,
                        response_format={"type": "json_object"},
                    )
                    model_used = client.model

            # 6. Parse and validate response
            message = self._parse_llm_response(response_text)

            logger.info(
                f"Generated message for customer {request.customer_id}: "
                f"subject='{message.subject[:30]}...'"
            )

            return MessageGenerationResponse(
                customer_id=request.customer_id,
                message=message,
                recommendations_used=[rec.name for rec in recommendations],
                model_used=model_used,
            )

        except (OpenRouterAPIKeyError, GroqAPIKeyError):
            logger.error(f"{request.llm_provider} API key not configured")
            raise

        except (OpenRouterError, GroqError) as e:
            logger.error(f"LLM API error for customer {request.customer_id}: {e}")
            raise MessageGenerationException(f"Failed to generate message: {str(e)}")

        except Exception as e:
            logger.error(
                f"Unexpected error generating message for customer {request.customer_id}: {e}"
            )
            raise MessageGenerationException(f"Message generation failed: {str(e)}")

    async def _get_customer(self, customer_id: UUID) -> Customer:
        """Fetch customer by ID"""
        result = await self.db.execute(select(Customer).where(Customer.id == customer_id))
        customer = result.scalar_one_or_none()

        if not customer:
            raise CustomerNotFoundError(f"Customer {customer_id} not found")

        return customer

    async def _get_recommendations(
        self, customer_id: UUID, limit: int
    ) -> List[RecommendationItem]:
        """Get personalized recommendations for customer"""
        try:
            recommendations, _ = await self.recommendation_engine.generate_recommendations(
                customer_id=customer_id,
                limit=limit,
                exclude_recent_days=30,
            )

            if not recommendations:
                raise InsufficientDataError(
                    f"No recommendations available for customer {customer_id}"
                )

            return recommendations

        except ValueError as e:
            # Customer or profile not found
            raise InsufficientDataError(str(e))

    async def _get_last_order_summary(self, customer_id: UUID) -> str:
        """Get summary of customer's most recent order"""
        # Get most recent order with items
        result = await self.db.execute(
            select(Order)
            .where(Order.customer_id == customer_id)
            .options(selectinload(Order.order_items))
            .order_by(Order.order_date.desc())
            .limit(1)
        )
        last_order = result.scalar_one_or_none()

        if not last_order:
            return "This customer hasn't ordered yet"

        # Extract item names
        item_names = [item.item_name for item in last_order.order_items]

        # Calculate days since order
        now = datetime.now(timezone.utc)
        order_date = last_order.order_date
        if order_date.tzinfo is None:
            order_date = order_date.replace(tzinfo=timezone.utc)

        days_since = (now - order_date).days

        return format_last_order_summary(
            last_order_date=order_date,
            last_order_items=item_names,
            days_since_order=days_since,
        )

    def _parse_llm_response(self, response_text: str) -> GeneratedMessage:
        """
        Parse and validate LLM JSON response.

        Args:
            response_text: Raw text response from LLM

        Returns:
            Validated GeneratedMessage

        Raises:
            MessageGenerationException: If parsing fails or validation fails
        """
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            # Free models sometimes truncate mid-response. Try to extract a
            # partial JSON object by closing any open string/brace.
            repaired = response_text.strip()
            # Close an unterminated string value then close the object
            if not repaired.endswith("}"):
                # Strip trailing partial word/whitespace after last '"'
                last_quote = repaired.rfind('"')
                if last_quote != -1:
                    repaired = repaired[:last_quote] + '"}'
                else:
                    repaired += '"}'
            try:
                data = json.loads(repaired)
                logger.warning("LLM response was truncated; repaired JSON for parsing")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                raise MessageGenerationException(
                    f"LLM returned invalid JSON: {response_text[:100]}"
                )

        # Clamp subject to 60 chars to tolerate models that ignore the limit
        if "subject" in data and isinstance(data["subject"], str):
            data["subject"] = data["subject"][:60]

        try:
            return GeneratedMessage(**data)
        except Exception as e:
            logger.error(f"LLM response failed validation: {e}")
            raise MessageGenerationException(
                f"Generated message failed validation: {str(e)}"
            )
