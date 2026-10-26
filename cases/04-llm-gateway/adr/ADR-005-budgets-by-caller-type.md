# ADR-005: Budgets per use case; behaviour depends on caller type; circuit breaker for runaways

- **Status:** Proposed
- **Date:** 2026-10-26
- **Case:** 04 · An LLM gateway that cut the bill (Google Cloud)
- **Related:** ADR-001, ADR-006

## Context

One weekend, an agent retried a failing tool call in a loop for 31 hours. Retries and the runaway were 7% of the month's spend, and nobody noticed until the invoice. A single global spending cap would have stopped interactive apps used by staff mid-shift.

## Decision

1. Every use case has a daily budget (`budget_usd_per_day`) and an `on_budget` behaviour.
2. **Interactive** use cases: page the owner at 80% and 100%; keep serving.
3. **Agents and batch:** notify at 80%; **stop** at 100%.
4. **Retries:** at most two, with exponential backoff, counted in the budget.
5. **Circuit breaker:** if one use case sends the same failing request 10 times in a minute, open the breaker for that use case and page the owner.
6. If the counter store (Memorystore) is unavailable: interactive calls fail open and are logged; agent and batch calls fail closed.

## Options considered

| Option | Why not chosen |
|---|---|
| One global cap | Stops people mid-task; doesn't find the runaway |
| Alerts only | The runaway ran over a weekend; alerts weren't acted on |
| Hard stop for everything | Interactive outages cost more than the tokens |

## Consequences

- Owners must set realistic budgets; budgets are reviewed monthly from usage records.
- A misconfigured budget can stop a batch job; jobs must be resumable.

## Verification

- Replay of the 31-hour loop against the gateway: breaker opens within about a minute.
- Chaos test: Memorystore unavailable; interactive calls succeed, agent calls wait.
