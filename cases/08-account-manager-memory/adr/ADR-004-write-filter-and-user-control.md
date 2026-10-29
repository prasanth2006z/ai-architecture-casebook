# ADR-004: Filter every write, confirm shared notes, and let people see and delete memories

- **Status:** Proposed
- **Date:** 2026-10-26
- **Case:** 08 · Memory for an account-manager assistant (AWS)
- **Related:** ADR-002

## Context

A contact's family health detail was extracted, stored indefinitely and included in a forwarded briefing.

## Decision

1. **Allow-list of note types** for account notes: business priorities, concerns, decision process, risks, commitments made, work communication preferences. Others are not stored.
2. **Deny-list, second layer:** extraction instructions exclude health, family, religion, politics, personal life and colleagues' performance; every extracted note is then checked with Amazon Bedrock Guardrails (denied topics, sensitive-information filters). Hits are dropped and logged without their text.
3. **Confirmation:** account notes (visible to the account team) are saved only after the AM confirms the exact text. Personal preferences may be saved automatically.
4. **User control:** "What do you remember about <account>?" lists notes with source (who, when, conversation); edit and delete are available; delete removes the record.

## Consequences

- Fewer notes are stored; each one is reviewed by a person.
- Guardrails configuration becomes part of the release bundle (Case 05).

## Verification

- Sensitive-detail test: nothing stored (hard gate).
- Delete test: deleted record no longer retrievable.
