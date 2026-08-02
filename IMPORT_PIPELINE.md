# Import Pipeline

## Stage A — File interpretation

1. Upload file → MinIO/S3
2. Compute SHA256; short-circuit identical content
3. Create `uploaded_files` + `import_snapshots` + `import_jobs`
4. Extract CSV/XLSX (PDF text when reliable)
5. Detect sheets, nonempty regions, candidate tables, header rows, column types
6. Build compact structural summary (masked)
7. Deterministic heuristics + LLM → `import_interpretations`
8. User previews sample normalized rows and corrects mapping
9. User confirms interpretation (`human_confirmed = true`)

## Stage B — Normalization and assessment

1. Apply confirmed interpretation
2. Persist every `raw_source_rows` row
3. Normalize date/amount/currency/description
4. Build identity fingerprints
5. Classify: new / unchanged / updated / possible_duplicate / conflict / missing / duplicate_within_file
6. Upsert `source_records` + versions
7. Create or link `canonical_financial_events`
8. Run transfer / refund / reimbursement heuristics
9. Run LLM categorization (skip unchanged content)
10. Run Splitwise overlap when source type is Splitwise (or bank after Splitwise exists)
11. Update assessment statuses
12. Recalculate affected analytics caches/materialized summaries if used

## Identity hierarchy

1. Native source ID + household + source type + scope + account/group
2. Stable deterministic key (no filename/row/import timestamp)
3. Probabilistic assessment + human review

## Fingerprints

- **Canonical identity fingerprint** — stable across nonessential edits
- **Content fingerprint** — changes when meaningful fields change

## Visibility

Every raw row remains visible regardless of pending/failed/excluded status. Overall UI statuses:

Imported, Processing, Assessed, Assessed with Warning, Needs Review, Pending Category, Pending Match, Unassessed, Excluded, Failed.

## Repeat imports

Full-history exports create a new snapshot. Unchanged rows update `last_seen_snapshot_id` only. Confirmed user decisions are never silently overwritten.
