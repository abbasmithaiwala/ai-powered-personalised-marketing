#!/bin/bash
# Setup test database for running pytest

set -e

echo "=========================================="
echo "Setting up Test Database"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Find docker command
DOCKER_CMD=""
if command -v docker &> /dev/null; then
    DOCKER_CMD="docker"
elif [ -f "/usr/local/bin/docker" ]; then
    DOCKER_CMD="/usr/local/bin/docker"
else
    echo -e "${RED}✗ Docker is not installed${NC}"
    echo "Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
    exit 1
fi

echo -e "${GREEN}✓ Docker is available${NC}"

# Find docker-compose
DOCKER_COMPOSE_CMD=""
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif [ -f "/usr/local/bin/docker-compose" ]; then
    DOCKER_COMPOSE_CMD="/usr/local/bin/docker-compose"
else
    echo -e "${YELLOW}! docker-compose not found, using docker compose${NC}"
    DOCKER_COMPOSE_CMD="$DOCKER_CMD compose"
fi

# Check if postgres container is running
if ! $DOCKER_CMD ps | grep -q postgres; then
    echo -e "${YELLOW}! Postgres container not running${NC}"
    echo "Starting Docker services..."
    cd .. && $DOCKER_COMPOSE_CMD up -d postgres && cd backend
    echo "Waiting for postgres to be ready..."
    sleep 5
fi

echo -e "${GREEN}✓ Postgres container is running${NC}"

# Get container ID
CONTAINER_ID=$($DOCKER_CMD ps --filter name=postgres --format "{{.ID}}" | head -1)

if [ -z "$CONTAINER_ID" ]; then
    echo -e "${RED}✗ Could not find postgres container${NC}"
    exit 1
fi

echo "Container ID: $CONTAINER_ID"

# Check if test database exists
echo "Checking if test database exists..."
DB_EXISTS=$($DOCKER_CMD exec $CONTAINER_ID psql -U user -d marketing_db -tAc "SELECT 1 FROM pg_database WHERE datname='marketing_db_test'" 2>/dev/null || echo "")

if [ -z "$DB_EXISTS" ]; then
    echo -e "${YELLOW}! Test database does not exist. Creating...${NC}"
    $DOCKER_CMD exec $CONTAINER_ID psql -U user -d marketing_db -c "CREATE DATABASE marketing_db_test;"
    echo -e "${GREEN}✓ Test database created${NC}"
else
    echo -e "${GREEN}✓ Test database already exists${NC}"
fi

# Run migrations on test database
echo "Running migrations on test database..."
# Use psycopg (synchronous) for migrations, not asyncpg
export DATABASE_URL=postgresql://user:pass@localhost:5432/marketing_db_test

if [ -d ".venv" ]; then
    source .venv/bin/activate
    alembic upgrade head
    echo -e "${GREEN}✓ Migrations applied to test database${NC}"
else
    echo -e "${RED}✗ Virtual environment not found${NC}"
    echo "Please create a virtual environment first:"
    echo "  python -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✓ Test database setup complete!${NC}"
echo "=========================================="
echo ""
echo "You can now run tests with:"
echo "  pytest tests/test_order_processor.py -v"
echo ""
