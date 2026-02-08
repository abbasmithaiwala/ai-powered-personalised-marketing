from uuid import uuid4
from sqlalchemy import Boolean, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

from app.models.base import Base, TimestampMixin


class Brand(Base, TimestampMixin):
    """Brand/Restaurant entity"""

    __tablename__ = "brands"

    id: Mapped[Uuid] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    slug: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
    )

    cuisine_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    menu_items: Mapped[List["MenuItem"]] = relationship(
        "MenuItem",
        back_populates="brand",
        cascade="all, delete-orphan",
    )

    orders: Mapped[List["Order"]] = relationship(
        "Order",
        back_populates="brand",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Brand(id={self.id}, name='{self.name}')>"
