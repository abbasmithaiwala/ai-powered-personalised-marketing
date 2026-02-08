# AI-Powered Personalised Marketing

End-to-end platform for food brands that ingests customer order data, builds dynamic preference profiles, generates personalized AI-driven marketing campaigns, and continuously learns from customer behavior.

## Stack

- **Backend:** Python 3.11+ / FastAPI
- **Database:** PostgreSQL 16 + Alembic migrations
- **Vector DB:** Qdrant
- **AI:** OpenRouter API (default: `anthropic/claude-3.5-sonnet`)
- **Frontend:** React 19 + TypeScript + Vite
- **Queue:** Redis

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

### Backend

```bash
cd backend
cp .env.example .env
# Edit .env with your values (at minimum set OPENROUTER_API_KEY)

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload
```

Health check: `GET http://localhost:8000/api/v1/health`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard: `http://localhost:5173`

### Full Stack (Docker)

Start all services (PostgreSQL, Qdrant, Redis, Backend):

```bash
docker compose up -d
```

Access the services:
- Backend API: `http://localhost:8000`
- Health check: `http://localhost:8000/api/v1/health`
- Qdrant dashboard: `http://localhost:6333/dashboard`
- PostgreSQL: `localhost:5432` (user/pass/marketing_db)

Stop all services:

```bash
docker compose down
```

View logs:

```bash
docker compose logs -f backend
```

## Project Structure

```
backend/
├── app/
│   ├── main.py          # FastAPI app factory
│   ├── core/            # Config, logging, exceptions
│   ├── api/v1/          # Route handlers
│   ├── models/          # SQLAlchemy ORM models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   ├── repositories/    # DB query layer
│   └── db/              # DB session, vector store
└── tests/
frontend/
└── src/
```

## Database Migrations

The project uses Alembic for database schema migrations.

### Apply migrations

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

### Rollback migrations

```bash
alembic downgrade base
```

### Create new migration

```bash
alembic revision --autogenerate -m "Description of changes"
```

## Running Tests

```bash
cd backend
pytest
```

## Development Status

### ✅ Completed Tasks

- **TASK-001:** Project Structure & Backend Skeleton
- **TASK-002:** Docker Compose Dev Environment
- **TASK-003:** Database Models & Alembic Migrations
  - 7 SQLAlchemy models created (Brand, MenuItem, Customer, Order, OrderItem, CustomerPreference, IngestionJob)
  - Initial migration with all tables, indexes, and foreign keys
  - All model tests passing

### 🔄 Next Tasks

- **TASK-004:** Qdrant Vector Store Setup
- **TASK-005:** CSV Schema Validation
- And more...
