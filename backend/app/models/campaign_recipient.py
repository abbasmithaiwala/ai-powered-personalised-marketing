"""Campaign recipient model for tracking individual campaign messages"""

from sqlalchemy import String, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from typing import Optional, Dict, Any

from app.models.base import Base, TimestampMixin


class CampaignRecipient(Base, TimestampMixin):
    """
    Represents an individual recipient in a campaign with their generated message.

    Each recipient has a personalized message generated specifically for them.
    """

    __tablename__ = "campaign_recipients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    generated_message: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Generated message with subject and body"
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        comment="pending | generated | failed"
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    campaign: Mapped["Campaign"] = relationship(
        "Campaign",
        back_populates="recipients"
    )
    customer: Mapped["Customer"] = relationship(
        "Customer",
        foreign_keys=[customer_id]
    )

    def __repr__(self) -> str:
        return f"<CampaignRecipient(id={self.id}, campaign_id={self.campaign_id}, status='{self.status}')>"
