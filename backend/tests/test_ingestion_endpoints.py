"""
Tests for ingestion API endpoints.

Tests CSV upload, validation, and job management endpoints.
"""

import io
from datetime import datetime
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingestion_job import IngestionJob


@pytest.mark.asyncio
class TestUploadCSV:
    """Test CSV upload endpoint."""

    async def test_upload_valid_csv(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test uploading a valid CSV file."""
        # Create valid CSV content
        csv_content = """order_id,customer_email,brand_name,item_name,quantity,unit_price,order_date
ORD001,john@example.com,Pizza Palace,Margherita Pizza,2,12.50,2024-01-15
ORD002,jane@example.com,Burger Joint,Classic Burger,1,8.99,2024-01-16
"""

        files = {"file": ("orders.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        data = {"csv_type": "orders"}

        response = await async_client.post("/api/v1/ingestion/upload", files=files, data=data)

        assert response.status_code == 200
        result = response.json()

        assert "job_id" in result
        assert result["status"] == "completed"
        assert result["total_rows"] == 2
        assert result["valid"] is True
        assert result["processed_rows"] == 2
        assert result["failed_rows"] == 0

    async def test_upload_csv_with_validation_errors(self, async_client: AsyncClient):
        """Test uploading CSV with validation errors."""
        # CSV with invalid data
        csv_content = """order_id,customer_email,brand_name,item_name,quantity,unit_price,order_date
ORD001,invalid-email,Pizza Palace,Margherita Pizza,2,12.50,2024-01-15
ORD002,jane@example.com,Burger Joint,Classic Burger,-1,8.99,bad-date
"""

        files = {"file": ("orders.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        data = {"csv_type": "orders"}

        response = await async_client.post("/api/v1/ingestion/upload", files=files, data=data)

        assert response.status_code == 200
        result = response.json()

        assert result["status"] == "failed"
        assert result["valid"] is False
        assert result["failed_rows"] > 0
        assert "validation_errors" in result
        assert len(result["validation_errors"]) > 0

    async def test_upload_csv_missing_required_columns(self, async_client: AsyncClient):
        """Test uploading CSV with missing required columns."""
        csv_content = """order_id,customer_email
ORD001,john@example.com
"""

        files = {"file": ("orders.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        data = {"csv_type": "orders"}

        response = await async_client.post("/api/v1/ingestion/upload", files=files, data=data)

        assert response.status_code == 400
        result = response.json()

        assert "detail" in result
        assert "missing_columns" in result["detail"]

    async def test_upload_non_csv_file(self, async_client: AsyncClient):
        """Test uploading non-CSV file returns 415."""
        files = {"file": ("test.txt", io.BytesIO(b"not a csv"), "text/plain")}
        data = {"csv_type": "orders"}

        response = await async_client.post("/api/v1/ingestion/upload", files=files, data=data)

        assert response.status_code == 415
        assert "CSV" in response.json()["detail"]

    async def test_upload_file_too_large(self, async_client: AsyncClient):
        """Test uploading file larger than max size."""
        # Create content larger than 50MB
        large_content = "a" * (51 * 1024 * 1024)

        files = {"file": ("large.csv", io.BytesIO(large_content.encode()), "text/csv")}
        data = {"csv_type": "orders"}

        response = await async_client.post("/api/v1/ingestion/upload", files=files, data=data)

        assert response.status_code == 413
        assert "too large" in response.json()["detail"].lower()

    async def test_upload_invalid_csv_type(self, async_client: AsyncClient):
        """Test uploading with invalid csv_type."""
        csv_content = "header1,header2\nvalue1,value2"

        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        data = {"csv_type": "invalid_type"}

        response = await async_client.post("/api/v1/ingestion/upload", files=files, data=data)

        assert response.status_code == 400
        assert "Invalid csv_type" in response.json()["detail"]


@pytest.mark.asyncio
class TestListJobs:
    """Test job listing endpoint."""

    async def test_list_jobs_empty(self, async_client: AsyncClient):
        """Test listing jobs when none exist."""
        response = await async_client.get("/api/v1/ingestion/jobs")

        assert response.status_code == 200
        result = response.json()

        assert result["items"] == []
        assert result["total"] == 0
        assert result["page"] == 1
        assert result["pages"] == 0

    async def test_list_jobs_with_data(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test listing jobs with existing data."""
        # Create test jobs
        job1 = IngestionJob(
            filename="test1.csv",
            csv_type="orders",
            status="completed",
            total_rows=100,
            processed_rows=100,
        )
        job2 = IngestionJob(
            filename="test2.csv",
            csv_type="orders",
            status="failed",
            total_rows=50,
            processed_rows=30,
            failed_rows=20,
        )

        db_session.add(job1)
        db_session.add(job2)
        await db_session.commit()

        response = await async_client.get("/api/v1/ingestion/jobs")

        assert response.status_code == 200
        result = response.json()

        assert len(result["items"]) == 2
        assert result["total"] == 2
        assert result["pages"] == 1

    async def test_list_jobs_pagination(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test job listing pagination."""
        # Create 30 test jobs
        for i in range(30):
            job = IngestionJob(
                filename=f"test{i}.csv",
                csv_type="orders",
                status="completed",
                total_rows=10,
            )
            db_session.add(job)

        await db_session.commit()

        # First page
        response = await async_client.get("/api/v1/ingestion/jobs?page=1&page_size=10")
        assert response.status_code == 200
        result = response.json()
        assert len(result["items"]) == 10
        assert result["total"] == 30
        assert result["pages"] == 3
        assert result["page"] == 1

        # Second page
        response = await async_client.get("/api/v1/ingestion/jobs?page=2&page_size=10")
        assert response.status_code == 200
        result = response.json()
        assert len(result["items"]) == 10
        assert result["page"] == 2

    async def test_list_jobs_invalid_page(self, async_client: AsyncClient):
        """Test listing with invalid page number."""
        response = await async_client.get("/api/v1/ingestion/jobs?page=0")
        assert response.status_code == 400

    async def test_list_jobs_invalid_page_size(self, async_client: AsyncClient):
        """Test listing with invalid page size."""
        response = await async_client.get("/api/v1/ingestion/jobs?page_size=0")
        assert response.status_code == 400

        response = await async_client.get("/api/v1/ingestion/jobs?page_size=101")
        assert response.status_code == 400


@pytest.mark.asyncio
class TestGetJob:
    """Test get job by ID endpoint."""

    async def test_get_job_success(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test getting job by ID."""
        job = IngestionJob(
            filename="test.csv",
            csv_type="orders",
            status="completed",
            total_rows=100,
            processed_rows=100,
        )

        db_session.add(job)
        await db_session.commit()
        await db_session.refresh(job)

        response = await async_client.get(f"/api/v1/ingestion/jobs/{job.id}")

        assert response.status_code == 200
        result = response.json()

        assert result["id"] == str(job.id)
        assert result["filename"] == "test.csv"
        assert result["status"] == "completed"
        assert result["total_rows"] == 100

    async def test_get_job_not_found(self, async_client: AsyncClient):
        """Test getting non-existent job returns 404."""
        fake_id = uuid4()
        response = await async_client.get(f"/api/v1/ingestion/jobs/{fake_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_get_job_invalid_uuid(self, async_client: AsyncClient):
        """Test getting job with invalid UUID format."""
        response = await async_client.get("/api/v1/ingestion/jobs/invalid-uuid")

        assert response.status_code == 422  # FastAPI validation error
