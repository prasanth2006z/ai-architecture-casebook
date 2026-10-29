# ADR-002: Never store CRM facts in memory; the CRM wins and conflicts are flagged

- **Status:** Proposed
- **Date:** 2026-12-07
- **Case:** 08 · Memory for an account-manager assistant (AWS)
- **Related:** Case 03 ADR-004 (source precedence)

## Context

A note naming a departed contact as champion outlived the CRM update. Memory duplicated a fact the CRM owns, and the copy went stale.

## Decision

1. Memory never stores system-of-record facts: contact roles and status, deal stage, amounts, contract dates, products owned.
2. The assistant reads these live from the CRM on every briefing.
3. At write time, a candidate note that is a CRM field is not stored; the assistant suggests updating the CRM.
4. At read time, a note that conflicts with the CRM is shown with a flag and the CRM value is used; the AM is asked whether to remove the note.

## Consequences

- Briefings always call the CRM; CRM latency affects briefing latency.
- Notes are limited to soft context, which is what the CRM can't hold.

## Verification

- Conflict test in the release gate: CRM value used, note flagged.
- Monthly: share of notes flagged as conflicting (target: falling).
