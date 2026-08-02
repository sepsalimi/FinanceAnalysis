# Splitwise Matching

## Principles

1. Splitwise amounts are estimates — never require exact equality.
2. Deterministic candidate retrieval precedes any LLM call.
3. Preserve both source records; count the economic event once.
4. Bank/card record is usually payment evidence; Splitwise is allocation evidence.

## Candidate window

Default: 3 days before → 7 days after Splitwise expense date. Wider for travel, foreign currency, hotels, delayed posting.

## Amount tolerances (candidate only)

- < 100 household currency units: absolute diff ≤ 10
- 100–500: ≤ 20% difference
- > 500: ≤ 15% difference
- Wider when merchant/payer/participants align strongly

## Confidence

- ≥ 0.95 single clear candidate, no conflict → may auto-link
- 0.75–0.94 → human review
- < 0.75 → unmatched
- One-to-many / many-to-one → always review
