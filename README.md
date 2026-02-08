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

```bash
docker-compose up -d
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

## Running Tests

```bash
cd backend
pytest
```
