# ADR-005: Above limits, a person decides through a task-token approval queue

- **Status:** Proposed
- **Date:** 2026-10-26
- **Case:** 06 · A support agent that can issue refunds (AWS)
- **Related:** Case 02 (review queue with `.waitForTaskToken`)

## Context

Some refunds need judgement: high value, frequent refunders, missing high-value items.

## Decision

1. Quotes over $150, a customer's 4th automatic refund in 90 days, or any refund while the daily cap or kill switch is active get status `needs_approval`.
2. A Step Functions workflow waits on a task token; a support lead approves or declines in a review screen showing the order, the conversation and the rules evaluated.
3. The agent tells the customer a person will review within four hours; the customer is notified of the outcome.

## Consequences

- Queue staffing becomes part of the service level.
- The review screen must show reasons, not only the transcript.

## Verification

- Queue age alarm at 4 hours.
- Sample of approvals reviewed monthly for consistency.
