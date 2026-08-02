# Data Model

PostgreSQL with UUID primary keys, UTC timestamps (`timestamptz`), and `NUMERIC` for money.

## Core identity

### user_accounts
Login identity: email, password hash, display name, active/verified flags, last login.

### households
Name, default currency, timezone, locale, confidence settings (JSON), analytics defaults (JSON), active flag.

### household_members
Display-name participants within a household. Optional link to `user_accounts`. Role semantics for the person profile (participant / admin / inactive). **No fixed person columns.**

### household_memberships
Join of user ↔ household ↔ member with permission role (`owner|administrator|member|read_only`).

## Accounts

### financial_institutions
Optional institution catalog (name, country, type).

### financial_accounts
Chequing, savings, credit card, LOC, loan, mortgage, investment, cash, other. Currency, ownership via primary member + allocation JSON, balances, net-worth/cash-flow inclusion flags.

### ownership_allocations
Reusable allocation structure (member percentages / household-level) referenced by accounts, events, recurring items, assets, debts.

## Import pipeline

### uploaded_files
Original file metadata, storage key, SHA256, size, detected source type, import/malware/deletion status.

### import_snapshots
Point-in-time view of an external source (including full-history Splitwise exports). Counts for new/unchanged/updated/duplicate/conflict/missing/failed.

### import_jobs
Background job tracking with stage, progress, errors/warnings, idempotency key, retries.

### import_interpretations
Proposed/confirmed structural mapping (sheet, range, columns JSON, amount convention, date format, LLM metadata).

### import_profiles
Reusable structural signatures per household/source; suggested only after re-validation.

### raw_source_rows
Exact extracted rows (`original_values` JSON), fingerprint, parsing status, link to source record.

### source_records
Stable external identity (`native_source_id`, `stable_source_key`, canonical/content fingerprints). Status: active, missing_from_latest_snapshot, deleted_at_source, reappeared, superseded, error.

### source_record_versions
Revision history with field differences.

## Canonical finance

### canonical_financial_events
Confirmed economic events: dates, type, merchant, amounts/currencies, category, household economic share, transfer/refund/reimbursement flags, analytics inclusion, overall assessment status.

### source_event_relationships
Links source records ↔ events with relationship type, confidence, evidence JSON, confirmation status.

### financial_event_allocations
Member and external participant paid/owed/net shares.

### transaction_splits
Category splits that must sum to the applicable amount (DB check + service validation).

## Taxonomy & AI

### merchants / merchant_aliases
Household or global merchants with confirmed aliases.

### categories
Parent/child taxonomy; system-seeded but editable.

### category_proposals
LLM proposals requiring human approval before category creation.

### categorization_assessments
Stored LLM/rule decisions with confidence, prompt version, provider/model, explanation.

### categorization_rules
Human-confirmed match rules with priority.

## Splitwise

### external_participants
People outside the household membership table.

### splitwise_expenses / splitwise_participant_allocations
Normalized Splitwise evidence.

### splitwise_overlap_assessments
Candidate matches with evidence hierarchy and review status.

## Planning & net worth

### recurring_cash_flow_items
Frequencies and annualized amounts (backend-calculated).

### planned_one_time_items
Planned/completed/cancelled/overdue items with optional linked events.

### assets / asset_snapshots
### debts / debt_snapshots
### budgets

## Audit

### audit_events
Who changed what, previous/new JSON, request/job IDs.

## Conventions

1. No `person_1_amount`-style columns.
2. No hardcoded member named Both/Shared/Couple.
3. Money: `NUMERIC(19, 4)` storage; display rounding in services/UI.
4. Soft flags (`is_active`, deletion status) preserve history.
5. Indexes on household_id, fingerprints, native source IDs, assessment status, event dates.
