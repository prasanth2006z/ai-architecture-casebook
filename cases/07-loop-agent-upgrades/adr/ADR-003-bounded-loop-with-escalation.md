# ADR-003: The loop is bounded in code and escalates with a useful note

- **Status:** Proposed
- **Date:** 2026-11-30
- **Case:** 07 · A loop agent that upgrades 300 repositories (Google Cloud)
- **Related:** Case 04 ADR-005 (budgets and circuit breaker)

## Context

Three pilot runs went ~40 iterations each for ~6 hours with no stop condition.

## Decision

1. Each iteration's input: first real verifier error (trimmed), diff so far, files named in the error, guard rejection reasons.
2. Loop code stops when: verifier green (open PR); 5 iterations used; the same first error appears twice in a row (no progress); token budget or 45 minutes used.
3. On stop without success, escalate to the owning team with: script changes, agent attempts, last error, agent's summary of the likely cause.
4. Implementation: ADK `LoopAgent` with `max_iterations` and an exit tool, or an ADK 2.0 graph workflow; stop rules are code with unit tests in either case.

## Consequences

- Worst-case cost and time per repository are known in advance.
- Some fixable repos are escalated early; the note makes the human fix faster.

## Verification

- Unit tests for each stop condition.
- No repository exceeds 5 iterations or 45 minutes in fleet logs.
