"""Message generation schemas for API requests and responses"""

from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from typing import List


class GeneratedMessage(BaseModel):
    """AI-generated marketing message"""

    subject: str = Field(..., description="Email subject line", max_length=60)
    body: str = Field(..., description="Email body text")

    @field_validator("body")
    @classmethod
    def validate_body_word_count(cls, v: str) -> str:
        """Ensure body is under 150 words"""
        word_count = len(v.split())
        if word_count > 150:
            raise ValueError(f"Body must be 150 words or less (got {word_count} words)")
        return v


class MessageGenerationRequest(BaseModel):
    """Request to generate a personalized message for a customer"""

    customer_id: UUID = Field(..., description="Customer to generate message for")
    campaign_purpose: str = Field(
        ...,
        description="Purpose/theme of the campaign (e.g., 'New menu launch', 'Weekend special')",
        min_length=5,
        max_length=200,
    )
    brand_group_name: str = Field(
        ...,
        description="Name of the brand or restaurant group",
        min_length=2,
        max_length=100,
    )
    offer: str | None = Field(
        None,
        description="Optional special offer or discount to mention",
        max_length=200,
    )
    recommendation_limit: int = Field(
        5,
        ge=1,
        le=10,
        description="Number of dish recommendations to include",
    )
    llm_provider: str = Field(
        "openrouter",
        description="LLM provider to use (openrouter | groq)",
    )
    llm_model: str | None = Field(
        None,
        description="Specific model to use (if None, uses provider default)",
    )


class MessageGenerationResponse(BaseModel):
    """Response containing generated message"""

    customer_id: UUID = Field(..., description="Customer ID")
    message: GeneratedMessage = Field(..., description="Generated message")
    recommendations_used: List[str] = Field(
        ...,
        description="Names of dishes that were recommended and used in generation",
    )
    model_used: str = Field(..., description="LLM model used for generation")


class MessageGenerationError(BaseModel):
    """Error details when message generation fails"""

    customer_id: UUID = Field(..., description="Customer ID")
    error_type: str = Field(..., description="Error type (e.g., 'no_profile', 'llm_error')")
    error_message: str = Field(..., description="Human-readable error message")
