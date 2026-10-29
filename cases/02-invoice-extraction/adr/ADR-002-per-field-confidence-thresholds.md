# ADR-002: Confidence thresholds per field, set by the cost of error

- **Status:** Accepted
- **Date:** 2026-10-26
- **Case:** 02 · Invoice extraction with human review (AWS)
- **Related:** ADR-001 (routing), ADR-005 (golden set and audit)

## Context

Field confidence is one of the routing checks (ADR-001). A single global threshold treats a misread invoice date the same as a misread total. Those errors do not cost the same: a wrong total is a wrong payment; a wrong vendor address is cosmetic.

## Decision

Each field has its own minimum confidence. Below it, that field (not the whole invoice) is flagged for review.

| Field | Cost if wrong | Starting threshold |
|---|---|---|
| Total, tax, line amounts | Wrong payment | 98 |
| Invoice number | Duplicate check fails | 97 |
| PO number | Wrong cost center | 95 |
| Invoice date, due date | Late fee or early payment | 90 |
| Vendor address, descriptions | Cosmetic | 80 |

Starting values are placeholders. Each threshold is tuned on the golden set to **the most auto-approval that keeps that field's escaped error rate under a limit agreed with finance**.

Thresholds live in configuration, versioned with the code, and change only through the release gate (ADR-005).

## Options considered

| Option | Why not chosen |
|---|---|
| One global threshold | Either too strict for cosmetic fields or too loose for amounts |
| Thresholds per vendor only | Useful later as an override (vendor watch list), but the cost of error is driven by the field first |

## Consequences

- Reviewers see only the fields that need them.
- Needs a golden set and periodic re-tuning, especially after an extractor change.
- Finance must agree a per-field escaped error limit before launch.

## Verification

- Tuning report per field: threshold vs straight-through rate vs escaped error rate on the golden set.
- Threshold changes blocked if any field exceeds its escaped error limit.
