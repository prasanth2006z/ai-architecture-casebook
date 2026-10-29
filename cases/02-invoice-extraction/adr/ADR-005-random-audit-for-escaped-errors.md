# ADR-005: Measure escaped errors with a random audit of auto-approved invoices

- **Status:** Accepted
- **Date:** 2026-10-26
- **Case:** 02 · Invoice extraction with human review (AWS)
- **Related:** ADR-001 (routing), ADR-002 (thresholds), ADR-003 (extractor swaps)

## Context

Invoices that go to review show how often reviewers correct the model. They say nothing about invoices that were auto-approved, and those are the ones that become wrong payments. A rising straight-through rate can look like progress while errors slip through.

## Decision

1. **Random audit.** 2% of invoices that would be auto-approved are sent to review anyway. The reviewer is not told the invoice was auto-approved.
2. **Corrections store.** Every review writes `(invoice, field, extracted value, corrected value, reason)`. Audit corrections are stored the same way.
3. **Metrics.**

| Metric | Definition | Purpose |
|---|---|---|
| Straight-through rate | % of invoices auto-approved | Business value |
| Escaped error rate | % of audited auto-approved invoices with any wrong field | Real risk |
| Field accuracy | Per field, extracted vs corrected | Threshold tuning |
| Review time | Median seconds per reviewed invoice | UI effectiveness |

4. **Uses of the corrections store:** golden set for extractor comparison and threshold tuning; vendor watch list (stricter thresholds for vendors corrected often); release gate for any change to extractor or thresholds.

5. **Rollout gates.** Shadow mode first (weeks 1–4, everything reviewed, route recorded). Then auto-approve for one vendor group. Widen group by group only after a full month under the escaped-error limit.

## Options considered

| Option | Why not chosen |
|---|---|
| Measure accuracy on reviewed invoices only | Biased; says nothing about auto-approved invoices |
| Rely on downstream payment complaints | Too late and incomplete |

## Consequences

- The audit adds review work on invoices that already passed.
- Gives the only unbiased estimate of escaped error rate.
- The escaped-error limit is a finance decision and must be agreed before launch.

## Verification

- Audit sample is drawn at random per invoice, not per vendor or time window.
- Dashboards show escaped error rate with its confidence interval, not just a point value.
