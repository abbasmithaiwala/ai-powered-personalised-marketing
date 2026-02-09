"""
Repository for ingestion job database operations.

Handles CRUD operations for ingestion jobs.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingestion_job import IngestionJob


class IngestionJobRepository:
    """Repository for ingestion job operations."""

    def __init__(self, db: AsyncSession):
        """Initialize repository with database session."""
        self.db = db

    async def create(
        self,
        filename: str,
        csv_type: str,
        total_rows: int,
        status: str = "pending",
        validation_errors: Optional[dict] = None,
    ) -> IngestionJob:
        """
        Create a new ingestion job.

        Args:
            filename: Name of uploaded CSV file
            csv_type: Type of CSV (e.g., "orders")
            total_rows: Total number of rows in CSV
            status: Job status (default: "pending")
            validation_errors: Optional validation errors

        Returns:
            Created IngestionJob instance
        """
        job = IngestionJob(
            filename=filename,
            csv_type=csv_type,
            total_rows=total_rows,
            status=status,
            processed_rows=0,
            failed_rows=0,
            validation_errors=validation_errors,
        )

        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)

        return job

    async def get_by_id(self, job_id: UUID) -> Optional[IngestionJob]:
        """
        Get ingestion job by ID.

        Args:
            job_id: Job UUID

        Returns:
            IngestionJob if found, None otherwise
        """
        result = await self.db.execute(select(IngestionJob).where(IngestionJob.id == job_id))
        return result.scalar_one_or_none()

    async def get_all(
        self,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[List[IngestionJob], int]:
        """
        Get all ingestion jobs with pagination.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (list of jobs, total count)
        """
        # Get total count
        count_result = await self.db.execute(select(IngestionJob))
        total = len(count_result.all())

        # Get paginated results
        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(IngestionJob).order_by(desc(IngestionJob.created_at)).offset(offset).limit(page_size)
        )
        jobs = result.scalars().all()

        return list(jobs), total

    async def update_status(
        self,
        job_id: UUID,
        status: str,
        processed_rows: Optional[int] = None,
        failed_rows: Optional[int] = None,
        validation_errors: Optional[dict] = None,
        result_summary: Optional[dict] = None,
    ) -> Optional[IngestionJob]:
        """
        Update ingestion job status and progress.

        Args:
            job_id: Job UUID
            status: New status
            processed_rows: Number of successfully processed rows
            failed_rows: Number of failed rows
            validation_errors: Validation errors encountered
            result_summary: Summary of processing results

        Returns:
            Updated IngestionJob if found, None otherwise
        """
        job = await self.get_by_id(job_id)
        if not job:
            return None

        job.status = status

        if processed_rows is not None:
            job.processed_rows = processed_rows

        if failed_rows is not None:
            job.failed_rows = failed_rows

        if validation_errors is not None:
            job.validation_errors = validation_errors

        if result_summary is not None:
            job.result_summary = result_summary

        await self.db.commit()
        await self.db.refresh(job)

        return job
