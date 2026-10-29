# ADR-002: Sync on change, reconcile on schedule

- **Status:** Accepted
- **Date:** 2026-11-02
- **Case:** 03 · Keeping a team knowledge assistant in sync (GCP)
- **Related:** ADR-001, ADR-003

## Context

Each source signals change differently. Bitbucket can send webhooks; Confluence supports CQL queries on `lastmodified`; schema changes arrive through migrations in the repository. Webhooks can be missed, and deletions and permission changes are easy to overlook.

## Decision

One trigger per source, plus a nightly reconcile:

| Source | Trigger | Action |
|---|---|---|
| Bitbucket | The deploy pipeline moves a `prod` tag to the deployed commit. Webhook on `repo:push` (tag change) → Cloud Run endpoint. Verify `X-Hub-Signature` (HMAC SHA-256 with the webhook secret) before doing anything. | Publish old and new commit to Pub/Sub; code indexer re-indexes the changed files (ADR-007). |
| Confluence | Cloud Scheduler every 15 minutes runs CQL, e.g. `space = CLM and lastmodified >= "<last run>"`. | Docs indexer re-fetches and re-chunks changed pages. |
| Schema | The `prod` tag moves and the diff touches the migrations folder; also nightly. | Schema indexer reads the catalog from a **read replica** and rebuilds the schema catalog and join graph. |
| All | Nightly reconcile (Cloud Scheduler → Cloud Run job). | List everything, compare with the index, re-index differences, remove deleted items, refresh restrictions. |

**Which code:** the index describes the commit **deployed to production** (the `prod` tag), because that is what troubleshooting questions are about. Optionally, `main` can be indexed as a second, clearly labelled "not yet released" set.

Rules:

1. **Idempotent.** Each item stores a content hash; unchanged items are skipped. Replaying an event is safe.
2. **Deletes are real.** Deleted pages, removed files and dropped columns are removed from the index (tombstoned), not left behind.
3. **Versioned.** Every chunk records its source version: commit SHA, Confluence page version, or schema snapshot time.
4. **Sync state is stored** (last successful run per source) so a failed run resumes from the right point.

## Options considered

| Option | Why not chosen |
|---|---|
| Full rebuild every night only | Up to a day stale; wasteful |
| Webhooks only | Missed deliveries and deletes go unnoticed |
| Confluence webhooks | Possible; polling with CQL is simpler to operate and 15 minutes is fresh enough |

## Consequences

- Freshness lag: minutes for code and schema, ≤15 minutes for Confluence, ≤1 day worst case via reconcile.
- Webhook endpoint must be public and authenticated by signature; secrets in Secret Manager.

## Verification

- Freshness lag per source on a dashboard; alert if over target.
- Test: delete a page → it disappears from search after the next reconcile at the latest.
- Test: replaying the same webhook twice changes nothing.
