# ADR-002: Meter every call to BigQuery before optimising

- **Status:** Proposed
- **Date:** 2026-10-26
- **Case:** 04 · An LLM gateway that cut the bill (Google Cloud)
- **Related:** ADR-001, ADR-003

## Context

Nobody can say which app, feature or team drives the bill. Without attribution, any optimisation is a guess, and savings can't be shown afterwards.

## Decision

1. For the first two weeks the gateway changes nothing: it passes calls through and records them.
2. One usage record per call, published to Pub/Sub and loaded into BigQuery:
   `time, caller, use_case, owner_team, model, mode, input_tokens, cached_tokens, output_tokens, latency_ms, status, retry_of, cache_layer, cost_usd, price_version`.
3. `cost_usd` is computed from a **versioned price table** in the gateway config; every record names its `price_version`.
4. Monthly reconcile of summed `cost_usd` against the Cloud Billing export; variance tracked.
5. The headline metric per use case is **cost per successful task**, not total spend.

## Options considered

| Option | Why not chosen |
|---|---|
| Billing export only | Shows SKUs and tokens, not callers or use cases |
| Request logs in Cloud Logging | Possible, but expensive to query and retain at volume; BigQuery is where finance already reports |
| Synchronous write to BigQuery | Couples request latency and availability to the analytics store |

## Consequences

- Metering is asynchronous; it never blocks a request (ADR-006).
- Cost is an estimate close enough to rank use cases; the invoice remains the source of truth for the total.
- Usage records contain no prompt or response text, only counts and metadata.

## Verification

- Every record has a non-empty `use_case` and `caller`.
- Monthly reconcile within 3% of the billing export (planning target).
