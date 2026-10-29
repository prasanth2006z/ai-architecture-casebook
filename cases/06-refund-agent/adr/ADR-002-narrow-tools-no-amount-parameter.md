# ADR-002: Narrow tools; reason codes; the amount is never a model parameter

- **Status:** Proposed
- **Date:** 2026-10-26
- **Case:** 06 · A support agent that can issue refunds (AWS)
- **Related:** ADR-003, ADR-004

## Context

`issue_refund(order_id, amount, reason)` let the model choose the amount, so a customer's claim ("plus 20%") became a refund.

## Decision

1. Tools: `list_my_orders()`, `get_my_order(order_id)`, `propose_refund(order_id, items, reason)`.
2. `reason` is one of `damaged`, `late`, `wrong_item`, `missing`, `not_as_described`.
3. The refund service computes the amount from the order (item prices; plus shipping if the whole order was late).
4. No tool issues or commits a refund.

## Consequences

- Goodwill gestures (vouchers, extra compensation) are out of scope for the agent; it hands those to a person.
- Fewer, simpler tools make the gateway policy short and reviewable.

## Verification

- Scenario: inflated amount claims always produce a quote at the computed amount.
