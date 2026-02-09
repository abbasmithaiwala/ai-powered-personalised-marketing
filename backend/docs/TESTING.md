# Testing Guide - Task 007

## Prerequisites

Before running tests, ensure you have:

1. **Docker Desktop installed and running**
   - Download from: https://www.docker.com/products/docker-desktop
   - Start Docker Desktop application

2. **Docker services running**
   ```bash
   # Start all services
   docker-compose up -d

   # Verify services are running
   docker ps
   # Should show: postgres, qdrant, redis, backend
   ```

3. **Virtual environment activated**
   ```bash
   cd backend
   source .venv/bin/activate
   ```

## Setup Test Database

### Option 1: Automated Setup (Recommended)

Run the setup script:
```bash
./setup_test_db.sh
```

This script will:
- Check if Docker is running
- Start postgres if not running
- Create `marketing_db_test` database
- Run migrations on test database

### Option 2: Manual Setup

If the script doesn't work, follow these steps:

1. **Start Docker services:**
   ```bash
   docker-compose up -d postgres
   ```

2. **Create test database:**
   ```bash
   # Get postgres container ID
   CONTAINER_ID=$(docker ps -q -f name=postgres)

   # Create test database
   docker exec $CONTAINER_ID psql -U user -d marketing_db -c "CREATE DATABASE marketing_db_test;"
   ```

3. **Run migrations on test database:**
   ```bash
   export DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/marketing_db_test
   alembic upgrade head
   ```

## Running Tests

### Run All Order Processor Tests

```bash
pytest tests/test_order_processor.py -v
```

### Run Specific Test

```bash
# Run a specific test class
pytest tests/test_order_processor.py::TestBrandResolver -v

# Run a specific test method
pytest tests/test_order_processor.py::TestOrderProcessor::test_process_single_order -v
```

### Run with Coverage

```bash
pytest tests/test_order_processor.py --cov=app.services.ingestion --cov-report=html
```

## Manual Testing

For manual verification without pytest:

```bash
python test_task007_manual.py
```

This script will:
- Connect to the main database
- Clean up test data
- Run a series of integration tests
- Print detailed results
- Verify all functionality works end-to-end

## Expected Test Results

When all tests pass, you should see:

```
tests/test_order_processor.py::TestBrandResolver::test_create_new_brand PASSED
tests/test_order_processor.py::TestBrandResolver::test_find_existing_brand_case_insensitive PASSED
tests/test_order_processor.py::TestCustomerResolver::test_create_new_customer PASSED
tests/test_order_processor.py::TestCustomerResolver::test_find_existing_customer_by_external_id PASSED
tests/test_order_processor.py::TestCustomerResolver::test_find_existing_customer_by_email PASSED
tests/test_order_processor.py::TestMenuItemResolver::test_create_new_menu_item PASSED
tests/test_order_processor.py::TestMenuItemResolver::test_find_existing_menu_item PASSED
tests/test_order_processor.py::TestOrderProcessor::test_process_single_order PASSED
tests/test_order_processor.py::TestOrderProcessor::test_process_multiple_orders_same_customer PASSED
tests/test_order_processor.py::TestOrderProcessor::test_idempotency_skip_duplicate_orders PASSED
tests/test_order_processor.py::TestOrderProcessor::test_calculate_order_total_when_missing PASSED
tests/test_order_processor.py::TestOrderProcessor::test_process_multiple_brands PASSED

======================== 12 passed in X.XXs ========================
```

## Troubleshooting

### Docker Not Running
```
Error: Cannot connect to the Docker daemon
```
**Solution:** Start Docker Desktop application

### Test Database Doesn't Exist
```
asyncpg.exceptions.InvalidCatalogNameError: database "marketing_db_test" does not exist
```
**Solution:** Run `./setup_test_db.sh` or create database manually (see above)

### Connection Refused
```
Connection refused (localhost:5432)
```
**Solution:**
- Check if postgres is running: `docker ps | grep postgres`
- Start services: `docker-compose up -d postgres`

### Migration Errors
```
sqlalchemy.exc.ProgrammingError: relation "brands" does not exist
```
**Solution:** Run migrations on test database:
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/marketing_db_test alembic upgrade head
```

### Import Errors
```
ModuleNotFoundError: No module named 'app'
```
**Solution:**
- Make sure you're in the `backend` directory
- Activate virtual environment: `source .venv/bin/activate`
- Install dependencies if needed: `pip install -e .`

## Cleaning Up

### Drop Test Database
```bash
docker exec $(docker ps -q -f name=postgres) psql -U user -d marketing_db -c "DROP DATABASE IF EXISTS marketing_db_test;"
```

### Stop Docker Services
```bash
docker-compose down
```

### Reset Everything
```bash
# Stop services and remove volumes
docker-compose down -v

# Restart fresh
docker-compose up -d
./setup_test_db.sh
```

## Test Coverage

Current test coverage for Task 007:

- **Brand Resolver:** 2 tests
- **Customer Resolver:** 3 tests
- **Menu Item Resolver:** 2 tests
- **Order Processor:** 5 tests
- **Total:** 12 tests

All core functionality is covered:
- ✓ Entity creation
- ✓ Entity resolution (find existing)
- ✓ Case-insensitive matching
- ✓ Idempotency
- ✓ Customer stats updates
- ✓ Multi-brand support
- ✓ Error handling
