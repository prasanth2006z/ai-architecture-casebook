# ADR-001: Separate kinds of memory; account notes are owned by the account

- **Status:** Proposed
- **Date:** 2026-12-07
- **Case:** 08 · Memory for an account-manager assistant (AWS)
- **Related:** ADR-003, ADR-005

## Context

Memory v1 stored all conversations per account manager. One person's memory covered ~40 accounts, notes blended across accounts, and knowledge was lost when the person moved on.

## Decision

1. Four kinds of memory: session (short-term events), preferences (per AM), account notes (per account), meeting summaries (per account).
2. Use Amazon Bedrock AgentCore Memory: short-term events for sessions; long-term records via built-in strategies (user preference for preferences; semantic extraction for account notes; summary for meetings).
3. Namespaces: `/users/{actorId}/preferences/` with `actorId = am_id`; `/accounts/{actorId}/notes/` and `/accounts/{actorId}/meetings/` with `actorId = account_id`.
4. Two memory resources (personal, account) so each has its own strategies and expiry.
5. On AM offboarding, delete their preference records; account records stay.

## Consequences

- New AMs inherit account knowledge immediately.
- Writes to account memory need the account ID resolved before the event is stored.

## Verification

- Handover test: reassigned account shows notes to the new AM; no old-AM preferences visible.
