# ADR-003: Put the extractor behind an adapter

- **Status:** Accepted
- **Date:** 2026-10-26
- **Case:** 02 · Invoice extraction with human review (AWS)
- **Related:** ADR-001 (routing), ADR-005 (golden set)

## Context

Two reasonable extraction options exist on AWS:

| Option | Strengths | Trade-offs |
|---|---|---|
| Textract AnalyzeExpense | Mature; standard field names (`TOTAL`, `INVOICE_RECEIPT_ID`, `VENDOR_NAME`); line items, bounding boxes, per-field confidence | Fixed schema; custom fields (PO formats, payment terms) need mapping |
| Bedrock Data Automation (custom blueprint) | You define fields and output shape; custom fields and validation rules in the blueprint | Newer; output can vary between documents, so downstream validation is still required |

Extraction quality will keep improving and the best option may change. Business rules should not move with it.

## Decision

Start with **Textract AnalyzeExpense**. Wrap any extractor in an adapter that returns one normalized `Invoice` object:

- fields and values (normalized dates, amounts, currency),
- per-field confidence on a 0–100 scale,
- page number and bounding box per field (for the review UI).

Checks, routing and review depend only on this object. Switching to BDA, or any other extractor, is an adapter change plus a golden-set comparison.

## Consequences

- Extractors can be compared on the same golden set and swapped without touching business rules.
- Confidence scales differ between services; the adapter must normalize them, and thresholds (ADR-002) must be re-tuned after a swap.
- One more layer to maintain.

## Verification

- Contract tests on the `Invoice` object for each adapter.
- Extractor swap goes through the release gate (ADR-005).
