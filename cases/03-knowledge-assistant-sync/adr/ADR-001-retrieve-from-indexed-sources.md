# ADR-001: Retrieve from indexed sources instead of a hand-built summary

- **Status:** Accepted
- **Date:** 2026-10-18
- **Case:** 03 · Keeping a team knowledge assistant in sync (GCP)
- **Related:** Case 01 · ADR-001 (hybrid search), Case 01 · ADR-003 (section-based chunking)

## Context

The team assistant answers questions about ClaimFlow (business process, tables, code, troubleshooting SQL) from one context document. A person builds it by collecting Confluence pages, table definitions and code, and asking ChatGPT to summarise them.

Problems:

- It is stale by default: freshness depends on someone remembering to rebuild it.
- It does not fit: one document cannot hold ~80 tables, the codebase and every spec, and summarising drops the details people ask about.
- It blends sources: spec (intent), code (behaviour) and schema (structure) are merged, so no one can tell where a statement came from.
- Answers have no citations, so they cannot be checked.

## Decision

Stop maintaining a hand-built context. The sources stay the source of truth:

- Index Confluence, code and schema into one store (Cloud SQL for PostgreSQL with pgvector, plus a structured schema catalog).
- The assistant retrieves per question and calls tools; it does not receive one large pre-written context.
- Every answer cites the page, file or table it used, with its version (ADR-006).

Summaries are allowed only as **derived, versioned artifacts** rebuilt by the pipeline when their input changes (for example, a per-module code summary). Nothing in the index is written by hand.

## Options considered

| Option | Why not chosen |
|---|---|
| Keep the hand-built summary, refresh on a calendar | Still stale between refreshes; still too big; no citations |
| Managed connector (e.g. Gemini Enterprise Confluence Cloud connector) for everything | Good for Confluence (full and incremental sync), but no Bitbucket connector listed and schema needs structured tools, not text search. Acceptable for the docs part only. |
| Fine-tune a model on the sources | Stale the day after training; no citations; expensive to repeat on every change |

## Consequences

- Answers become checkable and current, within the sync lag (ADR-002).
- The team now runs indexing pipelines.
- Retrieval quality must be measured (ADR-006).

## Verification

- No code path loads a hand-written context file.
- Citation rate tracked per answer.
