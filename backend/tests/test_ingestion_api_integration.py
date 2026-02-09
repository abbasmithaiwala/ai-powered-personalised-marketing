"""
Simple integration test for ingestion endpoints.

Tests that the endpoints are registered and basic validation works.
"""

import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_endpoint_exists(client: AsyncClient):
    """Test that upload endpoint is registered."""
    # This should fail with validation error (no file), not 404
    response = await client.post("/api/v1/ingestion/upload")
    assert response.status_code != 404, "Upload endpoint should exist"


@pytest.mark.asyncio
async def test_list_jobs_endpoint_exists(client: AsyncClient):
    """Test that list jobs endpoint is registered."""
    # Note: This will fail with DB error if tables don't exist, not 404
    # We're just checking the endpoint exists in routing
    response = await client.get("/api/v1/ingestion/jobs")
    # Should not be 404 (not found), could be 500 (DB error) which is fine for this test
    assert response.status_code != 404, "List jobs endpoint should exist"


@pytest.mark.asyncio
async def test_upload_requires_csv_file(client: AsyncClient):
    """Test that non-CSV file is rejected."""
    files = {"file": ("test.txt", io.BytesIO(b"not a csv"), "text/plain")}
    data = {"csv_type": "orders"}

    response = await client.post("/api/v1/ingestion/upload", files=files, data=data)

    # Should reject non-CSV files
    assert response.status_code == 415
    assert "CSV" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_validates_csv_type(client: AsyncClient):
    """Test that invalid csv_type is rejected."""
    files = {"file": ("test.csv", io.BytesIO(b"header1,header2\nval1,val2"), "text/csv")}
    data = {"csv_type": "invalid_type"}

    response = await client.post("/api/v1/ingestion/upload", files=files, data=data)

    # Should reject invalid csv_type
    assert response.status_code == 400
    assert "Invalid csv_type" in response.json()["detail"]
