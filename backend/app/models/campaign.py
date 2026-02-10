"""Campaign model for marketing campaign management"""

from sqlalchemy import String, Integer, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from typing import Optional, Dict, Any, List

from app.models.base import Base, TimestampMixin


class Campaign(Base, TimestampMixin):
    """
    Represents a marketing campaign.

    A campaign targets a segment of customers and generates personalized
    messages for each recipient.
    """

    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    purpose: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Campaign purpose used in message generation prompt"
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
        comment="draft | previewing | ready | executing | completed | failed"
    )
    segment_filters: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Filter criteria used to select recipients"
    )
    total_recipients: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    generated_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of messages generated so far"
    )

    # Relationships
    recipients: Mapped[List["CampaignRecipient"]] = relationship(
        "CampaignRecipient",
        back_populates="campaign",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Campaign(id={self.id}, name='{self.name}', status='{self.status}')>"
