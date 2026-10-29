# ADR-005: Waves with gates, exclude low-coverage repos from the agent, and require human review of agent changes

- **Status:** Proposed
- **Date:** 2026-11-30
- **Case:** 07 · A loop agent that upgrades 300 repositories (Google Cloud)
- **Related:** ADR-001, ADR-002

## Context

Pilot diffs were too large to review and mixed mechanical with real changes. A verifier is only as strong as the tests behind it.

## Decision

1. **Waves:** 10 low-risk internal repos → 50 → the rest; payment-path services last with owners pairing. A wave opens only if the previous one had no reverted merges and reviewers rejected fewer than 1 in 10 agent changes.
2. **Exclusion:** repos with test coverage below 40% get the script but never the agent.
3. **Pull requests:** two commits (script, agent); one-line reason per agent-changed file; test counts before/after; iterations; verifier link.
4. **Merge:** script-only and green → owner one-click merge, optional auto-merge after wave 1. Anything the agent touched → human review, always.

## Consequences

- Rollout takes longer than a single big push, and each wave produces evidence for the next.
- 22 repos (planning figure) are escalated without an agent attempt.

## Verification

- Wave gate metrics recorded before each wave opens.
- No agent-touched PR merged without an approving review (branch protection).
