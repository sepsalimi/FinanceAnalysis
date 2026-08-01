# Implementation Status

Last updated: 2026-08-01

## Overall

| Phase | Status | Notes |
|-------|--------|-------|
| Planning docs | Done | All required planning docs created |
| Phase 1 Foundation | Done | Auth, households, members, accounts, categories, Docker, design system |
| Phase 2 Dynamic imports | Done (MVP) | Upload, hash, extract CSV/XLSX, interpret, preview, confirm, raw rows |
| Phase 3 Canonical events | Done (MVP) | Fingerprints, source versions, relationships, transfer heuristic |
| Phase 4 Categorization/review | Done (MVP) | Stub/LLM assessments, review inbox, pending vs assessed |
| Phase 5 Splitwise | Partial | Models + docs + amount tolerance helpers; full overlap UI pending |
| Phase 6 Analytics | Done (MVP) | Dashboard + cash flow + category spend from confirmed DB records |
| Phase 7 Planning/net worth | Partial | Models + list APIs for assets/debts/planned items |
| Phase 8 Hardening | Partial | Backend tests green; Playwright scaffold pending expansion |

## Working vertical workflow checklist

- [x] Register / sign in
- [x] Create household + Person 1 (+ optional members)
- [x] Create financial account
- [x] Upload CSV/XLSX to object storage (or filesystem fallback)
- [x] Interpret file structure (deterministic + LLM/stub)
- [x] Preview/correct mapping and confirm
- [x] Persist raw rows, source records, canonical events
- [x] Idempotent re-import of identical content
- [x] LLM categorization with existing-category-first (stub provider)
- [x] Review inbox with assessed vs pending
- [x] Dashboard metrics from PostgreSQL

## Tests

- Backend: `pytest` — calculations, fingerprints, amount conventions, vertical workflow
- Frontend: typecheck/build
- E2E: Playwright package placeholder under `e2e/`

## Unfinished / deferred

1. OCR for scanned PDFs
2. Production malware scanner integration (interface status field present)
3. Full Splitwise overlap LLM review UI
4. Comprehensive Playwright suite for every edge case
5. Live FX rate provider
6. Moving normalize stage fully into Dramatiq with UI job polling (API currently runs normalize synchronously after confirm for reliability)
7. Export generation worker
8. Household hard/soft delete retention policy finalization

## Assumptions active in code

1. Dramatiq worker with Redis
2. Stub LLM provider when no API key configured
3. Filesystem object storage fallback when `STORAGE_FILESYSTEM_FALLBACK=true`
