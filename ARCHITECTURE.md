# Architecture

## Overview

```text
Browser (Next.js)
    │  HTTPS / REST /api/v1
    ▼
FastAPI API
    │──────────────► PostgreSQL (source of truth)
    │──────────────► Redis (queue + rate limits)
    │──────────────► MinIO / S3 (original files)
    │
    ▼
Dramatiq Worker
    ├── File extraction
    ├── Structure interpretation (deterministic + LLM)
    ├── Normalization / fingerprints
    ├── Duplicate / transfer / refund analysis
    ├── Categorization assessments
    ├── Splitwise overlap analysis
    ├── Analytics recalculation
    └── Export generation
```

## Principles

1. **Database first** — every financial number comes from PostgreSQL via documented services.
2. **LLM is advisory** — never creates categories or confirms matches without policy thresholds / human review.
3. **Provenance** — uploaded file → snapshot → raw row → source record → canonical event.
4. **Idempotent imports** — fingerprints and native IDs prevent duplicate economic events.
5. **Household isolation** — all queries scoped by household membership and role.
6. **Service layer** — route handlers stay thin; calculations live in `app/services`.

## Backend layers

| Layer | Responsibility |
|-------|----------------|
| `api/v1` | Auth, validation, HTTP mapping |
| `schemas` | Pydantic request/response models |
| `services` | Domain logic, calculations, import orchestration |
| `repositories` | Optional query helpers for heavy joins |
| `models` | SQLAlchemy 2 ORM |
| `workers` | Dramatiq background jobs |
| `llm` | Provider interface + structured output validation |
| `storage` | S3-compatible object storage |

## Worker choice: Dramatiq

**Why Dramatiq over Celery/RQ**

1. Redis broker already in the stack.
2. Simpler API and fewer moving parts than Celery for this job set.
3. Built-in retries, middleware, and actor priorities.
4. Easier local debugging than Celery’s broker/result complexity.
5. RQ is lighter but weaker for long-running multi-stage import pipelines with retries.

## Frontend architecture

- Next.js App Router, TypeScript strict mode
- TanStack Query for server state (no financial authority in client state)
- TanStack Table for review/transaction grids
- React Hook Form + Zod for forms
- Recharts for charts fed by analytics API responses
- Design tokens via CSS variables (ocean/teal theme, no purple primary)

## AuthZ model

- User account authenticates
- Household membership links user → household → household member profile
- Roles: `owner`, `administrator`, `member`, `read_only`
- Every entity carries `household_id` and is authorized through membership checks

## Observability

- Structured JSON logging with correlation/request IDs
- Import jobs expose stage + progress percentage
- Audit events for financial mutations
- Never log raw account numbers or full statement payloads
