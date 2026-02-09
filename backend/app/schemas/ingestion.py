"""
Pydantic schemas for ingestion API endpoints.

Request and response models for CSV upload and job management.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class IngestionJobCreate(BaseModel):
    """Request schema for creating an ingestion job (internal use)."""

    filename: str
    csv_type: str
    total_rows: int
    status: str = "pending"


class IngestionJobResponse(BaseModel):
    """Response schema for ingestion job."""

    id: UUID
    filename: Optional[str]
    csv_type: Optional[str]
    status: str
    total_rows: Optional[int]
    processed_rows: Optional[int]
    failed_rows: Optional[int]
    validation_errors: Optional[dict]
    result_summary: Optional[dict]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UploadResponse(BaseModel):
    """Response schema for CSV upload endpoint."""

    job_id: UUID = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Current job status")
    filename: str = Field(..., description="Uploaded filename")
    total_rows: int = Field(..., description="Total rows in CSV")
    validation_summary: str = Field(..., description="Validation result summary")
    valid: bool = Field(..., description="Whether CSV is valid")
    processed_rows: Optional[int] = Field(None, description="Rows processed (after completion)")
    failed_rows: Optional[int] = Field(None, description="Rows that failed (after completion)")
    validation_errors: Optional[list] = Field(None, description="List of validation errors")


class JobListResponse(BaseModel):
    """Response schema for job list endpoint."""

    items: list[IngestionJobResponse]
    total: int
    page: int
    page_size: int
    pages: int
