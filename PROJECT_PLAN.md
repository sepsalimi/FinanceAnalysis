# Project Plan — Household Financial Intelligence Platform

## Summary

Greenfield monorepo for a database-driven household finance platform. PostgreSQL is the source of truth. The LLM is an interpretation and assessment layer only. The first milestone is a complete vertical workflow: signup → household onboarding → account → file upload → LLM mapping preview → confirm import → normalize → categorize → review → analytics from confirmed records.

## Repository findings

- Existing repo contained only a placeholder `README.md` and `.gitignore`.
- No reusable application code was present.
- Stack chosen per specification (Next.js App Router + FastAPI + PostgreSQL + Redis + MinIO + Dramatiq).

## Folder structure

```text
/
├── README.md
├── PROJECT_PLAN.md
├── ARCHITECTURE.md
├── DATA_MODEL.md
├── FINANCIAL_CALCULATIONS.md
├── LLM_DESIGN.md
├── IMPORT_PIPELINE.md
├── DESIGN_SYSTEM.md
├── IMPLEMENTATION_STATUS.md
├── docker-compose.yml
├── .env.example
├── docs/
│   ├── API.md
│   ├── SPLITWISE_MATCHING.md
│   ├── DUPLICATE_PREVENTION.md
│   ├── BACKUP_RESTORE.md
│   ├── DEPLOYMENT.md
│   └── SECURITY.md
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── Dockerfile
│   ├── app/
│   │   ├── main.py
│   │   ├── core/           # config, security, logging, deps
│   │   ├── db/             # session, base, seed
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── api/v1/
│   │   ├── services/       # business logic (calc, import, llm, status)
│   │   ├── repositories/
│   │   ├── workers/        # Dramatiq tasks
│   │   ├── llm/            # provider abstraction
│   │   └── storage/        # S3/MinIO abstraction
│   ├── alembic/versions/
│   └── tests/
├── frontend/
│   ├── package.json
│   ├── Dockerfile
│   ├── src/app/
│   ├── src/components/
│   ├── src/lib/            # api client, money formatting
│   ├── src/hooks/
│   └── src/styles/
└── e2e/
    └── playwright/
```

## Phases

| Phase | Focus | Status target |
|-------|--------|---------------|
| 1 | Foundation: Docker, auth, households, members, accounts, categories, design system | Implement first |
| 2 | Dynamic imports: upload, extract, LLM interpret, preview, confirm, raw rows | Vertical path |
| 3 | Canonical events, fingerprints, duplicates, transfers/refunds | Vertical path |
| 4 | LLM categorization, review inbox, proposals, rules | Vertical path |
| 5 | Splitwise overlap matching | Core matching |
| 6 | Dashboard + analytics from confirmed DB records | Core metrics |
| 7 | Recurring, planned, assets, debts, forecast | Scaffold + APIs |
| 8 | Hardening, exports, deletion, monitoring | Ongoing |

## First vertical workflow

1. Register / sign in
2. Create household with Person 1 (+ optional people), currency, timezone
3. Create financial account
4. Upload CSV/XLSX
5. Store file in object storage, hash, create snapshot
6. Extract sheets/tables, propose interpretation (deterministic + LLM)
7. User corrects mapping and confirms
8. Persist raw rows → source records → canonical events
9. Detect duplicates / prior imports
10. LLM categorize (existing categories first)
11. Show assessed vs pending in Review
12. Dashboard metrics from confirmed PostgreSQL records

## Assumptions

1. Dramatiq + Redis is the task queue (simpler than Celery for this workload; Redis already required).
2. JWT access tokens in HTTP-only cookies for browser auth; Bearer tokens accepted for API clients.
3. Local LLM provider can be a deterministic stub when no API key is configured (tests/dev without external calls).
4. PDF support is text-extraction only; OCR for scanned PDFs is out of first release.
5. Multi-currency storage is supported; FX conversion tables are stubbed until rates are configured.
6. Malware scanning is integrated via a pluggable interface; local default is a no-op scanner that records status.
7. Default suggested currency may come from Accept-Language / locale hints, never hardcoded as the only option.

## Unresolved decisions

1. Exact cookie domain / SameSite policy for production reverse-proxy layouts.
2. Whether household deletion is hard-delete or soft-delete with retention window (leaning soft-delete + export-first).
3. Production object storage provider (AWS S3 vs compatible) — abstraction supports both.
4. Whether to add pgvector later for merchant/example retrieval; initial retrieval uses SQL similarity + aliases.

## Development commands

See `README.md` for the authoritative command list.
