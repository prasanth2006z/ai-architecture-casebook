# ADR-002: A fixed workflow in code with limits; agents do not decide the order of work

- **Status:** Proposed
- **Date:** 2026-10-26
- **Case:** 09 · One agent or five? A research assistant (Google Cloud)
- **Related:** Case 07 ADR-003 (loop control in code)

## Context

In the shared-conversation design, the order of work emerged from the conversation, making runs slow, unpredictable and hard to debug.

## Decision

1. Workflow: plan → search → code picks ≤ 12 sources → fetch and store → parallel readers → write → verify.
2. At most one revision pass; token budget per brief; time limit.
3. Implement with ADK as a sequential workflow with a parallel step (or an ADK 2.0 graph workflow). Limits are code with tests.
4. Store each step's input and output per run.

## Consequences

- Behaviour is predictable; cost per brief has a known ceiling.
- Less "creative" exploration; analysts can ask a follow-up question instead.

## Verification

- No run exceeds 12 sources or its budget.
- For any wrong brief, the failing step can be identified from stored step outputs.
