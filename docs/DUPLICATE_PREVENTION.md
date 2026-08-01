# Duplicate Prevention

## Identical files

SHA256 of file bytes. Same content (even with different filename) does not mutate financial state.

## Source identity

1. Native source ID (preferred)
2. Stable deterministic key
3. Probabilistic match + review

## Fingerprints

- Canonical identity fingerprint: stable across noise
- Content fingerprint: detects meaningful updates

## Classifications

New, Unchanged, Updated, Possible Duplicate, Conflict, Reappeared, Deleted at Source, Missing from Snapshot, Duplicate Within File.

## Human decisions

Confirmed categories, matches, rejections, exclusions, splits, notes, and rules survive later imports.
