from uuid import uuid4
from sqlalchemy import Integer, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class IngestionJob(Base, TimestampMixin):
    """CSV ingestion job tracking"""

    __tablename__ = "ingestion_jobs"

    id: Mapped[Uuid] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )

    filename: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    csv_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment='e.g., "orders"',
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        comment='pending | processing | completed | failed',
    )

    total_rows: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    processed_rows: Mapped[int | None] = mapped_column(
        Integer,
        default=0,
        nullable=True,
    )

    failed_rows: Mapped[int | None] = mapped_column(
        Integer,
        default=0,
        nullable=True,
    )

    validation_errors: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment='Array of error objects with row number and reason',
    )

    result_summary: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment='Summary of import results',
    )

    def __repr__(self) -> str:
        return f"<IngestionJob(id={self.id}, filename='{self.filename}', status='{self.status}')>"
