# ADR-004: Three cache layers, plus batch; never cache across user permissions

- **Status:** Proposed
- **Date:** 2026-10-26
- **Case:** 04 · An LLM gateway that cut the bill (Google Cloud)
- **Related:** Case 01 (access decided by data), ADR-003

## Context

18% of spend came from long prompts with the variable part first, so no reusable prefix formed. 9% came from a nightly job using the online API. 4% came from three apps summarising the same documents. A semantic cache was proposed as a general fix.

## Decision

1. **Prompt prefix caching (layer 1).** The gateway requires prompts in a fixed order: system instructions, shared documents, then user input. Gemini's implicit caching then bills the repeated prefix at a reduced rate. Use an explicit context cache with a TTL for large documents used all day.
2. **Exact-response cache (layer 2).** Only for use cases marked deterministic. Key = SHA-256 of model version, full prompt, parameters and the **data version** of every source used to build the prompt. TTL per use case.
3. **Semantic cache (layer 3).** Off by default. Allowed only for public, non-personal content (e.g. internal FAQ). **Never** for use cases filtered by user permissions.
4. **Batch.** Deferrable work (no deadline tighter than hours) uses batch inference.

## Options considered

| Option | Why not chosen |
|---|---|
| Semantic cache everywhere | Can return a wrong or unauthorised answer with full confidence |
| No caching | Leaves 20%+ of spend on the table |
| Exact cache without data version | Serves stale answers after a source document changes |

## Consequences

- Teams must order prompts correctly; the gateway rejects requests that break the order rule for use cases that declare a shared prefix.
- Batch jobs return in hours, not seconds; only use cases that accept that may use it.
- Cache correctness depends on callers passing a correct `data_version`.

## Verification

- Leak test: two users with different access asking the same question never receive the same cached answer.
- Cached-token share per use case tracked from usage records.
