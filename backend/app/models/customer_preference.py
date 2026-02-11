from uuid import uuid4
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class CustomerPreference(Base, TimestampMixin):
    """Customer preference profile computed from order history"""

    __tablename__ = "customer_preferences"

    id: Mapped[Uuid] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )

    customer_id: Mapped[Uuid] = mapped_column(
        Uuid,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    favorite_cuisines: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment='e.g., {"italian": 0.8, "thai": 0.6}',
    )

    favorite_categories: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment='e.g., {"mains": 0.9, "desserts": 0.5}',
    )

    dietary_flags: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment='e.g., {"vegetarian": true, "gluten_free": false}',
    )

    price_sensitivity: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="low | medium | high",
    )

    order_frequency: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="daily | weekly | monthly | occasional",
    )

    brand_affinity: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        comment='e.g., [{"brand_id": "...", "score": 0.9, "brand_name": "..."}]',
    )

    preferred_order_times: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment='e.g., {"breakfast": 0.2, "lunch": 0.5, "dinner": 0.8}',
    )

    last_computed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    # Relationships
    customer: Mapped["Customer"] = relationship(
        "Customer",
        back_populates="preference",
    )

    def __repr__(self) -> str:
        return f"<CustomerPreference(id={self.id}, customer_id={self.customer_id}, version={self.version})>"
