# ADR-006: Bound the blast radius: per-refund, per-customer and daily caps, a kill switch, and a 2% audit

- **Status:** Proposed
- **Date:** 2026-10-26
- **Case:** 06 · A support agent that can issue refunds (AWS)
- **Related:** Case 02 (random audit)

## Context

Per-refund checks can't catch an unknown failure that affects many refunds at once (a new manipulation technique, a bug in a rule).

## Decision

1. Automatic refund limit: $150 each; 3 per customer per 90 days.
2. Daily cap on automatic refunds across all customers: $8,000. Above it, quotes need approval and the team is paged.
3. Kill switch (feature flag): disables commits; agent continues to answer and quote, all quotes go to approval.
4. Every proposal and commit written to the audit log.
5. 2% random sample of automatic refunds reviewed by a person to measure the escaped wrongful-refund rate.

## Consequences

- Worst-case daily loss from an unknown failure is bounded.
- Limits must be reviewed as volume grows (at 10x, a rate per hour and region).

## Verification

- Game day: simulated spike of proposals trips the cap and pages the team.
- Monthly report: escaped wrongful-refund rate from the audit sample.
