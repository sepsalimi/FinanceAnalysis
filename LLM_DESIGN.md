# LLM Design

## Role

The LLM interprets file structures, suggests categories, and assesses Splitwise overlaps. PostgreSQL remains authoritative. The LLM never executes code from file contents.

## Provider abstraction

Interface in `backend/app/llm/base.py`:

- `OpenAIProvider`
- `AnthropicProvider`
- `GeminiProvider`
- `LocalProvider` (optional local HTTP)
- `StubProvider` (deterministic offline for tests/dev without keys)

Selected via `LLM_PROVIDER` env var. All calls are backend-only.

## Required metadata on every decision

Stored on interpretation / assessment rows:

1. Provider
2. Model
3. Prompt version
4. Confidence
5. Structured output JSON
6. Explanation
7. Source record / event linkage
8. Needs human review flag

## File interpretation

Input: compact structural summary (sheet names, candidate tables, header samples, inferred types, masked values).

Output: schema-constrained JSON validated by Pydantic (`FileInterpretationResult`).

User must confirm before Stage B normalization.

## Categorization

Policy: **existing categories first**. New categories create `category_proposals` and leave events in `pending_category`.

Confidence defaults (household-configurable):

| Range | Behavior |
|-------|----------|
| ≥ 0.90 | Auto-accept if no conflict and existing category |
| 0.70–0.89 | Needs review |
| < 0.70 | Remain pending |
| New category | Always review |

## Splitwise overlap

Deterministic candidate retrieval first (date window, amount proximity, description/merchant). LLM scores candidates only.

Auto-link only at ≥ 0.95 with a single clear candidate and no conflict. Amount similarity alone never confirms.

## Privacy

Do not send full statements, full account numbers, addresses, auth secrets, or unrelated household data. Mask PAN-like digits before any provider call.

## Prompt versioning

Prompt templates live under `backend/app/llm/prompts/` with explicit version strings (e.g. `file_interpret_v1`, `categorize_v1`, `splitwise_overlap_v1`).
