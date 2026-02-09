"""
Ingestion API endpoints.

Handles CSV file uploads, validation, and processing job management.
"""

import math
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.ingestion_job import IngestionJobRepository
from app.schemas.csv_schemas import ValidationError
from app.schemas.ingestion import (
    IngestionJobResponse,
    JobListResponse,
    UploadResponse,
)
from app.services.csv_validator import CSVValidator

router = APIRouter(prefix="/ingestion", tags=["ingestion"])

# Maximum file size: 50MB
MAX_FILE_SIZE = 50 * 1024 * 1024


@router.post("/upload", response_model=UploadResponse, status_code=200)
async def upload_csv(
    file: UploadFile = File(..., description="CSV file to upload"),
    csv_type: str = Form(..., description='CSV type (currently only "orders" is supported)'),
    db: AsyncSession = Depends(get_db),
) -> UploadResponse:
    """
    Upload and validate a CSV file.

    This endpoint:
    1. Validates the file type and size
    2. Validates the CSV structure and content
    3. Creates an ingestion job record
    4. In MVP: processes synchronously (for production: would queue for async processing)

    Args:
        file: CSV file upload
        csv_type: Type of CSV ("orders")
        db: Database session

    Returns:
        Upload response with job ID and validation results

    Raises:
        HTTPException 415: If file is not a CSV
        HTTPException 413: If file is too large
        HTTPException 400: If CSV validation fails
    """
    # Validate file type
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=415, detail="File must be a CSV (.csv extension)")

    # Validate CSV type
    if csv_type not in ["orders"]:
        raise HTTPException(status_code=400, detail=f'Invalid csv_type: "{csv_type}". Only "orders" is supported.')

    # Read file content
    content = await file.read()

    # Check file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024:.0f}MB",
        )

    # Decode content
    try:
        content_str = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")

    # Validate CSV
    validator = CSVValidator()
    validation_result = validator.validate_csv_file(content_str)

    # If validation failed due to missing columns, return error immediately
    if validation_result.has_missing_columns:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Missing required columns",
                "missing_columns": validation_result.missing_columns,
                "available_columns": list(validation_result.column_mapping.keys()),
                "message": validation_result.error_summary,
            },
        )

    # Create ingestion job
    repo = IngestionJobRepository(db)

    # Prepare validation errors for storage
    validation_errors_dict = None
    if validation_result.errors:
        validation_errors_dict = {
            "errors": [
                {
                    "row": err.row,
                    "field": err.field,
                    "error": err.error,
                    "value": err.value,
                }
                for err in validation_result.errors
            ],
            "total_errors": len(validation_result.errors),
        }

    # Determine initial status
    # For MVP: we process synchronously, so status will be updated after processing
    # For now, create job with validation status
    initial_status = "completed" if validation_result.valid else "failed"

    job = await repo.create(
        filename=file.filename,
        csv_type=csv_type,
        total_rows=validation_result.total_rows,
        status=initial_status,
        validation_errors=validation_errors_dict,
    )

    # Update job with results
    result_summary = {
        "valid_rows": validation_result.valid_rows,
        "invalid_rows": validation_result.invalid_rows,
        "validation_passed": validation_result.valid,
    }

    await repo.update_status(
        job_id=job.id,
        status=initial_status,
        processed_rows=validation_result.valid_rows,
        failed_rows=validation_result.invalid_rows,
        result_summary=result_summary,
    )

    # Refresh job to get updated data
    job = await repo.get_by_id(job.id)

    # Prepare validation errors for response (limited to first 100)
    response_errors = None
    if validation_result.errors:
        response_errors = [
            {"row": err.row, "field": err.field, "error": err.error, "value": err.value}
            for err in validation_result.errors[:100]
        ]

    return UploadResponse(
        job_id=job.id,
        status=job.status,
        filename=job.filename,
        total_rows=validation_result.total_rows,
        validation_summary=validation_result.error_summary
        if not validation_result.valid
        else f"Valid CSV with {validation_result.valid_rows} rows",
        valid=validation_result.valid,
        processed_rows=job.processed_rows,
        failed_rows=job.failed_rows,
        validation_errors=response_errors,
    )


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    page: int = 1,
    page_size: int = 25,
    db: AsyncSession = Depends(get_db),
) -> JobListResponse:
    """
    List all ingestion jobs with pagination.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)
        db: Database session

    Returns:
        Paginated list of ingestion jobs
    """
    if page < 1:
        raise HTTPException(status_code=400, detail="Page must be >= 1")

    if page_size < 1 or page_size > 100:
        raise HTTPException(status_code=400, detail="Page size must be between 1 and 100")

    repo = IngestionJobRepository(db)
    jobs, total = await repo.get_all(page=page, page_size=page_size)

    pages = math.ceil(total / page_size) if total > 0 else 0

    return JobListResponse(
        items=[IngestionJobResponse.model_validate(job) for job in jobs],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/jobs/{job_id}", response_model=IngestionJobResponse)
async def get_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> IngestionJobResponse:
    """
    Get a specific ingestion job by ID.

    Args:
        job_id: Job UUID
        db: Database session

    Returns:
        Ingestion job details

    Raises:
        HTTPException 404: If job not found
    """
    repo = IngestionJobRepository(db)
    job = await repo.get_by_id(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return IngestionJobResponse.model_validate(job)
