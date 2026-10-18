# ADR-001: Route invoices on verified checks, not model confidence

- **Status:** Accepted
- **Date:** 2026-10-17
- **Case:** 02 · Invoice extraction with human review (AWS)
- **Related:** Case 01 · ADR-002 (access control in retrieval: security comes from verified data, never from model output)

## Context

Supplier invoices arrive as PDFs, scans and phone photos. The goal is to extract fields automatically and send only uncertain invoices to a person.

Extraction services return a confidence score per field. That score says whether characters were *read* correctly, not whether the invoice should be *paid*. An invoice read with 99.9% confidence can still be a duplicate, unrelated to any open purchase order, or a request to pay a new bank account.

## Decision

Extraction output is a **claim**. Routing is decided by **deterministic checks against our own data**. No model takes part in the routing decision.

### Checks

| Check | Rule | On failure |
|---|---|---|
| Arithmetic | Line items sum to subtotal; subtotal + tax = total (±0.01 per line) | Review |
| Vendor match | Vendor found in vendor master **by tax ID**, never by name | Review |
| Purchase Order (PO) match | PO exists, is open, amount within tolerance of remaining PO value | Review |
| Duplicate | Same vendor + invoice number, or same vendor + amount within 30 days | **Hard stop** |
| Bank details | Bank account equals the one in vendor master | **Hard stop** |
| Field confidence | Each field above its own threshold (ADR-002) | Review (that field) |
| Format | Dates valid and not in the future; currency matches vendor | Review |

### Routing order

1. Duplicate or bank mismatch → **Hard stop**.
2. Any other failed check → **Review**, with reasons attached.
3. Amount above the auto-approve limit → **Review**.
4. Selected for the random audit sample (ADR-005) → **Review**.
5. Otherwise → **Auto-approve**.

There is no path where high confidence skips a check.

### Bank details are never updated from an invoice

A mismatch goes to a separate queue that only vendor management can clear, after confirming by phone using a number already on file. Four-eyes rule applies.

## Options considered

| Option | Why not chosen |
|---|---|
| Single global confidence threshold | Passes duplicates and fraud that were read with high confidence |
| LLM judge decides whether the invoice is correct | Non-deterministic, hard to audit, and puts payment safety on model output (conflicts with Case 01 · ADR-002) |
| Review every invoice | Safe but removes most of the value; used only as shadow mode during rollout |

## Consequences

- Every routing decision is explainable as a list of failed checks.
- Fraud and duplicate controls cannot be weakened by a better extractor or a tuned threshold.
- Check quality depends on vendor master and PO data; stale master data shows up as review volume.

## Verification

- Router unit tests: each failed check maps to the expected route; any failed hard-stop check routes to Hard stop regardless of confidence or amount.
- No code path reads confidence before the hard-stop checks run.
