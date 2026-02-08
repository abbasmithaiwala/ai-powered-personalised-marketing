from uuid import uuid4
from datetime import datetime
from sqlalchemy import DECIMAL, DateTime, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

from app.models.base import Base, TimestampMixin


class Customer(Base, TimestampMixin):
    """Customer entity"""

    __tablename__ = "customers"

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

    email: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    first_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    last_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    total_orders: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    total_spend: Mapped[float] = mapped_column(
        DECIMAL(12, 2),
        default=0,
        nullable=False,
    )

    first_order_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_order_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    orders: Mapped[List["Order"]] = relationship(
        "Order",
        back_populates="customer",
        cascade="all, delete-orphan",
    )

    preference: Mapped["CustomerPreference"] = relationship(
        "CustomerPreference",
        back_populates="customer",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Customer(id={self.id}, email='{self.email}')>"
