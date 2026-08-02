# Household Financial Intelligence Platform

Database-driven household finance application: QuickBooks-style review plus modern analytics. PostgreSQL is the source of truth. The LLM is an interpretation and assessment layer only.

## Run in the cloud (recommended)

You do **not** need to run this on your laptop.

GitHub Pages alone cannot host Postgres/API. Use the Render Blueprint for the full app on one public URL:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/sepsalimi/FinanceAnalysis)

1. Sign up at [render.com](https://render.com) (free tier works for a personal deploy).
2. Click **Deploy to Render** above (or Dashboard → New → Blueprint → this repo).
3. Approve the `render.yaml` resources (Postgres + Redis + web app).
4. Open the service URL Render gives you (example shape: `https://finance-app.onrender.com`).
5. Register, onboard your household, optionally paste an LLM API key in **Household Settings**, then upload bank/Splitwise files.
6. On your phone, open that same URL → **Add to Home Screen** / **Install app**.

Details and free-tier limits: [`docs/CLOUD_DEPLOY.md`](docs/CLOUD_DEPLOY.md).

## What the cloud app includes

- UI + API on the same HTTPS URL
- PostgreSQL (source of truth)
- Redis for queue/support infra
- Multi-file CSV/XLSX uploads per account + Splitwise
- Per-file structure analysis (correctable before import)
- LLM keys stored encrypted in the database (never in git)
- Installable phone PWA

## Stack

- Frontend: Next.js App Router, TypeScript, Tailwind, TanStack Query/Table, Recharts, RHF, Zod
- Backend: FastAPI, SQLAlchemy 2, Alembic, Pydantic
- Worker: Dramatiq + Redis (optional in cloud; imports also run synchronously)
- Storage: filesystem fallback in cloud; S3/MinIO compatible
- Database: PostgreSQL

## Optional: GitHub Pages UI mirror

Static UI: https://sepsalimi.github.io/FinanceAnalysis/

Pages is UI-only. Prefer the Render URL for real imports and login.

## Optional: local Docker

```bash
cp .env.example .env
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API docs | http://localhost:8000/docs |
| MinIO console | http://localhost:9001 |

## Common commands (local/dev)

```bash
cd backend && alembic upgrade head
cd backend && python -m app.db.seed
cd backend && pytest
cd frontend && npm test && npm run typecheck && npm run build
```

## Documentation

- `docs/CLOUD_DEPLOY.md` — cloud hosting
- `PROJECT_PLAN.md`, `ARCHITECTURE.md`, `DATA_MODEL.md`
- `FINANCIAL_CALCULATIONS.md`, `LLM_DESIGN.md`, `IMPORT_PIPELINE.md`
- `DESIGN_SYSTEM.md`, `IMPLEMENTATION_STATUS.md`

## Security notes

Never commit `.env` files or API keys. Configure LLM keys in Household Settings (encrypted in Postgres) or as Render env vars.
