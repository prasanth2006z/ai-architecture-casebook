# ADR-003: Refund rules live in the refund service; AgentCore Policy at the gateway is a second check

- **Status:** Proposed
- **Date:** 2026-11-23
- **Case:** 06 · A support agent that can issue refunds (AWS)
- **Related:** ADR-002, ADR-006

## Context

Rules written only in the prompt can be argued with. Rules written only in a gateway policy mix business logic into security configuration. We need both layers, with different jobs.

## Decision

1. **AgentCore Policy** (Cedar policies in a policy engine attached to AgentCore Gateway; generally available March 2026) decides which tools this agent may call and validates inputs: default deny; allow the three tools; `reason` must be one of five codes.
2. **The refund service** decides eligibility and amount: ownership, reason, 30-day window, not already refunded, amount calculation, automatic limits, kill switch. Implemented as ordinary code with unit tests per rule.
3. The prompt describes the rules (generated from the same config file) so the agent can explain them, but does not enforce them.

## Options considered

| Option | Why not chosen |
|---|---|
| Rules in the prompt | Can be talked around; not testable as code |
| All rules in gateway policy | Business logic (amounts, windows) belongs with the data it needs |

## Consequences

- Two places to update when tools change; both reviewed together.
- If prompt and service disagree, the service wins and the agent reports its decision.

## Verification

- Policy test: a call to any tool other than the three is denied.
- Unit tests cover every rule boundary (day 30/31, $150.00/$150.01, 3rd/4th refund).
