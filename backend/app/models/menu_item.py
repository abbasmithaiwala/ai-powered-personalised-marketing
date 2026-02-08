from uuid import uuid4
from sqlalchemy import Boolean, DECIMAL, ForeignKey, String, Text, Uuid, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

from app.models.base import Base, TimestampMixin


class MenuItem(Base, TimestampMixin):
    """Menu item entity"""

    __tablename__ = "menu_items"

    id: Mapped[Uuid] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )

    brand_id: Mapped[Uuid] = mapped_column(
        Uuid,
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    cuisine_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    price: Mapped[float | None] = mapped_column(
        DECIMAL(10, 2),
        nullable=True,
    )

    dietary_tags: Mapped[List[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )

    flavor_tags: Mapped[List[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )

    is_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    embedding_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Relationships
    brand: Mapped["Brand"] = relationship(
        "Brand",
        back_populates="menu_items",
    )

    order_items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="menu_item",
    )

    def __repr__(self) -> str:
        return f"<MenuItem(id={self.id}, name='{self.name}', brand_id={self.brand_id})>"
