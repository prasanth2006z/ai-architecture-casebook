# ADR-001: Customer identity comes from the session; tools filter by it

- **Status:** Proposed
- **Date:** 2026-10-26
- **Case:** 06 · A support agent that can issue refunds (AWS)
- **Related:** Case 01 (access decided by data), ADR-002

## Context

In red-team testing the agent refunded another customer's order after the user claimed to be helping a relative. The tool accepted any order ID and the service account could read every order.

## Decision

1. Customers sign in (Cognito) before chatting; the chat backend holds a verified identity.
2. AgentCore Gateway passes the signed-in customer's identity to every tool call. No tool accepts a customer ID from the model.
3. Order tools filter by that identity. An order that belongs to someone else returns `not_found`, indistinguishable from a missing order.
4. Requests on behalf of others are handled by a human agent, not the AI agent.

## Consequences

- Guest-checkout customers must sign in or use a verified email link before refunds.
- The model can't be talked into reaching another customer's data, whatever the prompt says.

## Verification

- Scenario tests: other customer's order ID in any phrasing → no quote created.
- Tool logs show customer ID always sourced from the session token.
