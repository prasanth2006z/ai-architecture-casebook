# ADR-003: Chunk by policy section, not by fixed token count

Status: Accepted · Date: 2026-10-09

## Context
HR policies are structured documents with numbered sections. A fixed 500-token split can separate an entitlement or a condition ("only after 12 months of service") from the rule it qualifies.

## Decision
Split on section headings. Sections longer than about 1,000 tokens are split again on sub-headings, keeping the parent heading as a prefix. Every chunk carries document title, section number, country, grade band, version and effective date as metadata.

## Alternatives rejected
- Fixed-size chunks with overlap: simple, but breaks rules from their conditions; overlap duplicates text and cost.
- Whole document per chunk: precise citations become impossible and long documents dilute relevance.
- LLM-based semantic chunking: adds ingestion cost and non-deterministic boundaries for little gain on documents that already have clear structure.

## Consequences
Needs a parser that understands headings. Badly formatted documents fall back to fixed-size splitting and are flagged to HR. Section hit rate in the shared harness measures whether this decision pays off (POC 1).

## Revisit when
Retrieval tests show answers failing because the needed text spans several sections.
