"""Base types and schemas for AI services."""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class Message(BaseModel):
    """OpenAI-compatible message format."""
    role: Literal["system", "user", "assistant"]
    content: str


class CompletionRequest(BaseModel):
    """Request schema for LLM completion."""
    messages: List[Message]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1, le=8192)
    response_format: Optional[dict] = None  # For JSON mode: {"type": "json_object"}


class CompletionResponse(BaseModel):
    """Response schema for LLM completion."""
    content: str
    model: str
    tokens_used: Optional[int] = None
