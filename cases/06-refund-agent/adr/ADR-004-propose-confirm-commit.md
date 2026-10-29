# ADR-004: Propose, confirm, commit; the customer's click commits; quote ID is the idempotency key

- **Status:** Proposed
- **Date:** 2026-10-26
- **Case:** 06 · A support agent that can issue refunds (AWS)
- **Related:** ADR-002, ADR-005

## Context

A timeout after the payment API accepted a refund caused the agent to retry and refund twice. A model that can commit money can also be talked into committing it.

## Decision

1. **Propose:** the agent calls `propose_refund`; the service returns a quote (ID, items, amount, reason, status, expiry in 15 minutes).
2. **Confirm:** the chat UI shows the quote as a card with a *Confirm refund* button. Chat text ("yes") does not count.
3. **Commit:** the click goes from the UI backend (with the customer's session) to the refund service, which re-checks rules and expiry, then calls the payment provider with the quote ID as the idempotency key.
4. The agent has no commit capability; it learns the outcome from the service.

## Consequences

- A retry with the same quote ID cannot refund twice.
- Customers who abandon the chat leave expired quotes; nothing moves.

## Verification

- Scenario: double submission → one payment.
- Scenario: "just type yes" → no commit.
