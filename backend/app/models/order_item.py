from uuid import uuid4
from sqlalchemy import DECIMAL, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class OrderItem(Base):
    """Order item entity (line item in an order)"""

    __tablename__ = "order_items"

    id: Mapped[Uuid] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )

    order_id: Mapped[Uuid] = mapped_column(
        Uuid,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    menu_item_id: Mapped[Uuid | None] = mapped_column(
        Uuid,
        ForeignKey("menu_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    item_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    unit_price: Mapped[float | None] = mapped_column(
        DECIMAL(10, 2),
        nullable=True,
    )

    subtotal: Mapped[float | None] = mapped_column(
        DECIMAL(10, 2),
        nullable=True,
    )

    # Relationships
    order: Mapped["Order"] = relationship(
        "Order",
        back_populates="order_items",
    )

    menu_item: Mapped["MenuItem"] = relationship(
        "MenuItem",
        back_populates="order_items",
    )

    def __repr__(self) -> str:
        return f"<OrderItem(id={self.id}, item_name='{self.item_name}', quantity={self.quantity})>"
