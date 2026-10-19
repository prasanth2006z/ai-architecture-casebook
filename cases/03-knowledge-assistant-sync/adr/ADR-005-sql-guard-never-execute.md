# ADR-005: Validate generated SQL against the live schema; never execute it

- **Status:** Accepted
- **Date:** 2026-10-18
- **Case:** 03 · Keeping a team knowledge assistant in sync (GCP)
- **Related:** ADR-003 (schema catalog)

## Context

Troubleshooting SQL is the most-used and riskiest output. With stale knowledge, SQL either fails (renamed column) or, worse, runs and returns the wrong rows (missing status value).

## Decision

Every generated query passes a guard before it is shown:

1. **Parse** (PostgreSQL dialect). Exactly one statement.
2. **Read-only.** The statement must be a query; no `INSERT`, `UPDATE`, `DELETE`, `MERGE`, DDL or commands anywhere, including inside CTEs.
3. **Schema check.** Every table and column must exist in the current schema catalog (CTE names allowed).
4. **EXPLAIN** on the read replica under a read-only role with a statement timeout, to catch type errors and very expensive plans.
5. On failure, the error goes back to the model for a limited number of retries.

Status values come from `list_status_values`, not from model memory, so new statuses appear as soon as the reference table changes.

The query is **shown, not executed**. A person runs it against the read replica. The assistant has no database credentials that can write, and never connects to the primary.

Reference implementation: `src/sql_guard.py` (uses sqlglot).

## Options considered

| Option | Why not chosen |
|---|---|
| Let the assistant run queries and return results | Risk of expensive queries on production and exposure of personal data in chat |
| Regex-based checks | Easy to bypass; cannot resolve aliases or CTEs |
| Prompt instructions only ("only write SELECT") | Model output is not a control |

## Consequences

- Catches loud failures (unknown table or column) before anyone sees them.
- Silent failures (missing status values) are reduced by sourcing values from the catalog, not removed entirely; the golden set tracks them.
- Small latency cost per SQL answer.

## Verification

- Unit tests: writes, multiple statements, writes inside CTEs, unknown tables and columns are rejected; valid joins and CTEs pass.
- SQL validity rate (first-try pass) tracked.
