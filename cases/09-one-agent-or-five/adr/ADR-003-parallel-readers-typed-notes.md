# ADR-003: Parallel readers with isolated contexts return typed notes; the writer cites note IDs

- **Status:** Proposed
- **Date:** 2026-10-26
- **Case:** 09 · One agent or five? A research assistant (Google Cloud)
- **Related:** ADR-004

## Context

Citation errors came from prose hand-offs; recall loss came from one context holding many pages.

## Decision

1. One reader per source, run in parallel. Each sees only the question, the sub-questions and its one page.
2. Readers have **no tools**; they return notes only.
3. Note schema: `note_id`, `source_id` (assigned by code before the reader runs), verbatim `quote`, `claim`, `about_date`.
4. The writer sees only notes (never pages) and must cite **note IDs**. Code converts note IDs to links after writing.

## Consequences

- The writer cannot invent URLs.
- Instructions hidden in a page have no tools to misuse.

## Verification

- Writer output contains no URLs (check).
- Reader configuration has an empty tool list (check).
