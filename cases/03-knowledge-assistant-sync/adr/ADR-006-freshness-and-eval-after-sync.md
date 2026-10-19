# ADR-006: Show freshness on every answer; evaluate after every sync

- **Status:** Accepted
- **Date:** 2026-10-18
- **Case:** 03 · Keeping a team knowledge assistant in sync (GCP)
- **Related:** ADR-002; Case 05 (evaluation as a release gate)

## Context

An automated pipeline can also break things automatically: a bad parser change, a failed sync, or a schema change that makes answers wrong. Users need to know how current an answer is.

## Decision

1. **Freshness on every answer.** Each answer lists its sources with versions, e.g. "Schema: claims, claim_status_history · snapshot today 09:10", "Confluence: CLM / Partial approval · v14, edited 2 h ago", "Code: src/domain/claimStatus.js · prod @ a1b2c3d".
2. **Golden set.** About 50 real questions from new joiners and past incidents, each with expected sources and, for SQL questions, required tables and status values.
3. **Evaluate after every sync.** The new index is built alongside the current one. If the golden-set pass rate drops beyond a threshold, the new index is not switched on and the team is alerted.
4. **Metrics.** Freshness lag per source, citation rate, SQL validity rate, golden-set pass rate.

## Consequences

- Index switch is blue/green, so storage roughly doubles during a sync.
- The golden set must be maintained; new incidents add questions.

## Verification

- Dashboard with the four metrics.
- Test: a deliberately broken index (e.g. schema catalog missing a table) is not promoted.
