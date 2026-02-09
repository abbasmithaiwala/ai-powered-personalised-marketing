#!/usr/bin/env python3
"""
Manual test script for TASK-006 ingestion endpoints.

This script verifies all acceptance criteria for the CSV upload API.
"""

import asyncio
import sys
from pathlib import Path

import httpx


BASE_URL = "http://localhost:8000"
API_KEY = "changeme"


async def test_upload_valid_csv():
    """Test uploading a valid CSV file."""
    print("\n=== Test 1: Upload Valid CSV ===")

    csv_path = Path(__file__).parent / "tests/fixtures/sample_orders_valid.csv"

    if not csv_path.exists():
        print(f"❌ CSV file not found: {csv_path}")
        return False

    async with httpx.AsyncClient() as client:
        with open(csv_path, "rb") as f:
            files = {"file": ("sample_orders_valid.csv", f, "text/csv")}
            data = {"csv_type": "orders"}
            headers = {"X-API-Key": API_KEY}

            response = await client.post(
                f"{BASE_URL}/api/v1/ingestion/upload", files=files, data=data, headers=headers
            )

        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 200:
            result = response.json()
            assert "job_id" in result, "Missing job_id in response"
            assert result["status"] in ["completed", "pending", "processing"], f"Unexpected status: {result['status']}"
            assert result["total_rows"] == 5, f"Expected 5 rows, got {result['total_rows']}"
            assert result["valid"] is True, "CSV should be valid"
            print("✅ Test passed")
            return True
        else:
            print(f"❌ Test failed with status {response.status_code}")
            return False


async def test_upload_invalid_csv():
    """Test uploading CSV with validation errors."""
    print("\n=== Test 2: Upload Invalid CSV ===")

    csv_path = Path(__file__).parent / "tests/fixtures/sample_orders_invalid.csv"

    if not csv_path.exists():
        print(f"❌ CSV file not found: {csv_path}")
        return False

    async with httpx.AsyncClient() as client:
        with open(csv_path, "rb") as f:
            files = {"file": ("sample_orders_invalid.csv", f, "text/csv")}
            data = {"csv_type": "orders"}
            headers = {"X-API-Key": API_KEY}

            response = await client.post(
                f"{BASE_URL}/api/v1/ingestion/upload", files=files, data=data, headers=headers
            )

        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 200:
            result = response.json()
            assert result["valid"] is False, "CSV should be invalid"
            assert result["failed_rows"] > 0, "Should have failed rows"
            assert "validation_errors" in result, "Should have validation errors"
            print("✅ Test passed")
            return True
        else:
            print(f"❌ Test failed with status {response.status_code}")
            return False


async def test_upload_missing_columns():
    """Test uploading CSV with missing required columns."""
    print("\n=== Test 3: Upload CSV with Missing Required Columns ===")

    csv_content = b"order_id,customer_email\nORD001,test@example.com"

    async with httpx.AsyncClient() as client:
        files = {"file": ("missing_columns.csv", csv_content, "text/csv")}
        data = {"csv_type": "orders"}
        headers = {"X-API-Key": API_KEY}

        response = await client.post(f"{BASE_URL}/api/v1/ingestion/upload", files=files, data=data, headers=headers)

        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 400:
            result = response.json()
            assert "detail" in result, "Should have error detail"
            assert "missing_columns" in result["detail"], "Should list missing columns"
            print("✅ Test passed")
            return True
        else:
            print(f"❌ Expected 400, got {response.status_code}")
            return False


async def test_upload_non_csv():
    """Test uploading non-CSV file returns 415."""
    print("\n=== Test 4: Upload Non-CSV File ===")

    async with httpx.AsyncClient() as client:
        files = {"file": ("test.txt", b"not a csv", "text/plain")}
        data = {"csv_type": "orders"}
        headers = {"X-API-Key": API_KEY}

        response = await client.post(f"{BASE_URL}/api/v1/ingestion/upload", files=files, data=data, headers=headers)

        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 415:
            print("✅ Test passed")
            return True
        else:
            print(f"❌ Expected 415, got {response.status_code}")
            return False


async def test_upload_file_too_large():
    """Test uploading file larger than max size."""
    print("\n=== Test 5: Upload File Too Large ===")

    # Create content larger than 50MB
    large_content = b"a" * (51 * 1024 * 1024)

    async with httpx.AsyncClient(timeout=30.0) as client:
        files = {"file": ("large.csv", large_content, "text/csv")}
        data = {"csv_type": "orders"}
        headers = {"X-API-Key": API_KEY}

        response = await client.post(f"{BASE_URL}/api/v1/ingestion/upload", files=files, data=data, headers=headers)

        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 413:
            print("✅ Test passed")
            return True
        else:
            print(f"❌ Expected 413, got {response.status_code}")
            return False


async def test_list_jobs():
    """Test listing jobs endpoint."""
    print("\n=== Test 6: List Jobs ===")

    async with httpx.AsyncClient() as client:
        headers = {"X-API-Key": API_KEY}
        response = await client.get(f"{BASE_URL}/api/v1/ingestion/jobs", headers=headers)

        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 200:
            result = response.json()
            assert "items" in result, "Should have items"
            assert "total" in result, "Should have total"
            assert "page" in result, "Should have page"
            assert "page_size" in result, "Should have page_size"
            print("✅ Test passed")
            return True
        else:
            print(f"❌ Expected 200, got {response.status_code}")
            return False


async def test_get_job(job_id: str):
    """Test getting a specific job by ID."""
    print(f"\n=== Test 7: Get Job {job_id} ===")

    async with httpx.AsyncClient() as client:
        headers = {"X-API-Key": API_KEY}
        response = await client.get(f"{BASE_URL}/api/v1/ingestion/jobs/{job_id}", headers=headers)

        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 200:
            result = response.json()
            assert result["id"] == job_id, "Job ID should match"
            print("✅ Test passed")
            return True
        else:
            print(f"❌ Expected 200, got {response.status_code}")
            return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("TASK-006 CSV Upload API - Manual Test Suite")
    print("=" * 60)

    tests = [
        ("Upload Valid CSV", test_upload_valid_csv()),
        ("Upload Invalid CSV", test_upload_invalid_csv()),
        ("Upload Missing Columns", test_upload_missing_columns()),
        ("Upload Non-CSV", test_upload_non_csv()),
        ("Upload Too Large", test_upload_file_too_large()),
        ("List Jobs", test_list_jobs()),
    ]

    results = []
    job_id = None

    for name, test_coro in tests:
        try:
            result = await test_coro
            results.append((name, result))

            # Capture job_id from first test
            if name == "Upload Valid CSV" and result:
                # Re-run to get job_id
                csv_path = Path(__file__).parent / "tests/fixtures/sample_orders_valid.csv"
                async with httpx.AsyncClient() as client:
                    with open(csv_path, "rb") as f:
                        files = {"file": ("sample_orders_valid.csv", f, "text/csv")}
                        data = {"csv_type": "orders"}
                        headers = {"X-API-Key": API_KEY}
                        response = await client.post(
                            f"{BASE_URL}/api/v1/ingestion/upload", files=files, data=data, headers=headers
                        )
                        if response.status_code == 200:
                            job_id = response.json()["job_id"]

        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((name, False))

    # Test get job if we have a job_id
    if job_id:
        try:
            result = await test_get_job(job_id)
            results.append(("Get Job by ID", result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(("Get Job by ID", False))

    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
