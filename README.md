# Household Financial Intelligence Platform

Database-driven household finance application: QuickBooks-style review plus modern analytics. PostgreSQL is the source of truth. The LLM is an interpretation and assessment layer only.

## Stack

- Frontend: Next.js App Router, TypeScript, Tailwind, TanStack Query/Table, Recharts, RHF, Zod
- Backend: FastAPI, SQLAlchemy 2, Alembic, Pydantic
- Worker: Dramatiq + Redis (chosen for a simpler Redis actor model than Celery while supporting retries for import pipelines)
- Storage: MinIO / S3 compatible (local filesystem fallback supported)
- Database: PostgreSQL

## Quick start (Docker Compose)

```bash
cp .env.example .env
docker compose up --build
```

Services:

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API docs | http://localhost:8000/docs |
| MinIO console | http://localhost:9001 (minioadmin / minioadmin) |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

## Local development without Docker

```bash
# infrastructure (example: local packages)
# ensure PostgreSQL and Redis are running, then:

cp .env.example .env
cd backend
uv venv .venv && source .venv/bin/activate
uv pip install -e ".[dev]"
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload --port 8000
```

Worker:

```bash
cd backend && source .venv/bin/activate
dramatiq app.workers.tasks --processes 1 --threads 2
```

Frontend:

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

## Common commands

```bash
# Migrations
cd backend && alembic upgrade head

# Seed system categories / taxonomy
cd backend && python -m app.db.seed

# Backend tests
cd backend && pytest

# Frontend typecheck / build
cd frontend && npm run typecheck
cd frontend && npm run build

# Frontend unit tests (when configured)
cd frontend && npm test

# End-to-end tests
cd e2e && npx playwright test

# API documentation
open http://localhost:8000/docs

# MinIO
open http://localhost:9001

# Reset local environment safely
docker compose down -v
# or drop/recreate local databases finance_dev / finance_test
```

## First vertical workflow

1. Register and sign in
2. Onboard a household (Person 1 required; more people optional)
3. Create a financial account
4. Upload a CSV/XLSX statement
5. Review/correct the LLM/heuristic interpretation
6. Confirm import
7. Inspect transactions and review statuses
8. View dashboard metrics calculated from confirmed PostgreSQL records

## Documentation

- `PROJECT_PLAN.md`
- `ARCHITECTURE.md`
- `DATA_MODEL.md`
- `FINANCIAL_CALCULATIONS.md`
- `LLM_DESIGN.md`
- `IMPORT_PIPELINE.md`
- `DESIGN_SYSTEM.md`
- `IMPLEMENTATION_STATUS.md`
- `docs/` — API, Splitwise matching, duplicates, backup, deployment, security

## GitHub Pages

The frontend static export is deployed from `main` via `.github/workflows/deploy-github-pages.yml`.

- Site URL: `https://<owner>.github.io/FinanceAnalysis/`
- GitHub Pages hosts the UI only. The FastAPI/PostgreSQL backend must be deployed separately; set repository variable `NEXT_PUBLIC_API_BASE_URL` to your API origin if the UI should call a remote backend.
- Local full-stack use remains `docker compose up --build` or the non-Docker commands above.

## Security notes

Never commit `.env` files or API keys. LLM credentials stay server-side. Uploaded files are treated as untrusted input.
