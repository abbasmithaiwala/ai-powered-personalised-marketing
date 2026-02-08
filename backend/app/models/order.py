from uuid import uuid4
from datetime import datetime
from sqlalchemy import DECIMAL, DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

from app.models.base import Base, TimestampMixin


class Order(Base, TimestampMixin):
    """Order entity"""

    __tablename__ = "orders"

    id: Mapped[Uuid] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )

    external_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )

    customer_id: Mapped[Uuid] = mapped_column(
        Uuid,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    brand_id: Mapped[Uuid] = mapped_column(
        Uuid,
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    order_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    total_amount: Mapped[float | None] = mapped_column(
        DECIMAL(10, 2),
        nullable=True,
    )

    channel: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # Relationships
    customer: Mapped["Customer"] = relationship(
        "Customer",
        back_populates="orders",
    )

    brand: Mapped["Brand"] = relationship(
        "Brand",
        back_populates="orders",
    )

    order_items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, external_id='{self.external_id}', customer_id={self.customer_id})>"
