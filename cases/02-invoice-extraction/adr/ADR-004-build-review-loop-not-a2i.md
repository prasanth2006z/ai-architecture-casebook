# ADR-004: Build the review loop in-house instead of using Amazon A2I

- **Status:** Accepted
- **Date:** 2026-10-26
- **Case:** 02 · Invoice extraction with human review (AWS)
- **Related:** ADR-001 (what gets reviewed)

## Context

Amazon Augmented AI (A2I) was the usual AWS answer for human review. In June 2026 AWS announced that A2I (with SageMaker Ground Truth) is moving to maintenance; it stopped accepting new customers on 2026-07-30. A new system should not depend on it.

Review must also be fast. A first screen that showed all 25 fields led reviewers to re-check everything, which took almost as long as re-keying.

## Decision

Build a small review loop:

- **Step Functions** pauses the workflow at the review step with `.waitForTaskToken`.
- **DynamoDB** holds the queue: invoice ID, reasons, assigned reviewer, SLA timestamp, task token.
- **Review UI** behind **Cognito** shows the PDF with bounding boxes **only around flagged fields**, with the reason for each.
- The UI calls **`SendTaskSuccess`** with the corrected invoice; the workflow continues to the ERP.

Rules:

1. Reviewers must confirm or correct **every** flagged field; no one-click approve.
2. Hard stops (ADR-001) use a separate queue and role, with a four-eyes rule.
3. Every correction is written to the corrections store (ADR-005).

## Options considered

| Option | Why not chosen |
|---|---|
| Amazon A2I | Maintenance mode, closed to new customers |
| Show all fields to reviewers | Slow; reviewers re-check everything |
| Third-party review tool | Possible, but adds a vendor for a small, well-defined loop |

## Consequences

- We own the UI, auth, queue and SLA tracking.
- Task tokens need timeouts and an escalation path for invoices left in the queue.
- Review screen can be designed for speed (flagged fields only).

## Verification

- Median review time per invoice tracked (ADR-005).
- Test: an invoice cannot leave review while any flagged field is untouched.
- Check AWS service status for A2I before publishing or revisiting this decision.
