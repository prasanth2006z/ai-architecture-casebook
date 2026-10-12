# ADR-001: Shared evaluation harness metric and entitlement definitions

Status: Proposed · Date: 2026-10-11

## Context
<!-- PLACEHOLDER (T004): drafted by Claude; the author rewrites this section before the ADR is accepted. -->
Every case study backs its numbers with evaluation output, so each POC needs the same metrics computed the same way. The harness lives in `shared/evals/` and is reused by all case studies. Spec: `specs/001-eval-harness/spec.md`.

## Decision
The harness follows these definitions. Rationale and detail are in `specs/001-eval-harness/research.md`.

- **Question files** are JSONL, one question per line, validated strictly (unknown keys are rejected).
- **Plug-in API**: a POC passes plain functions, wrapped in a named `Configuration`, for retrieval and optionally for answering. No framework or base class.
- **Document-level hit rate at k is the primary metric.** Section hit rate at k is secondary. A result without a section never matches an expected section; section hit rate is "n/a" only when no result in a configuration carries a section.
- **Percentiles** use the nearest-rank method (research R4).
- **Unified error rule**: any question recorded as an error counts as a miss for hit rate, section hit rate and MRR, as failed for the answer-based metrics, stays in every denominator, and is excluded from the latency percentiles. Error handling never lowers the cross-entitlement total.
- **Fail-closed entitlement rule**: a returned result with a missing, empty or non-text document id counts as a cross-entitlement retrieval (entitlement cannot be verified) and marks its question as an error (stage `validate`). Entitlement matching is exact and case-sensitive, and covers all returned results regardless of rank or expected document.
- **"n/a" metrics** (zero questions in a category) are shown as "n/a" with a notes line below the table explaining each one.

## Alternatives rejected
<!-- PLACEHOLDER (T004): drafted by Claude; the author rewrites this section before the ADR is accepted. -->
- JSON array or YAML question files: noisier diffs, or an extra dependency.
- Error counted only as an error, without counting an unverifiable result as a cross-entitlement retrieval: could hide a real cross-entitlement retrieval.
- Normalized entitlement matching (case, whitespace): could hide a real match or invent one.
- Top-k only entitlement counting: understates the count.
- Interpolated percentiles: depend on the method chosen and are harder to explain.

## Consequences
- Results are comparable across configurations and case studies, and one rule covers every error.
- The cross-entitlement count means "results proven forbidden or not provably allowed", so it can exceed the number of documents on the not-entitled list.
- With small question sets, p95 equals the maximum latency.
- Quality metrics (hit rate, section hit rate, MRR@k) use the top k results only; the cross-entitlement check uses all returned results, regardless of rank.
- Monitor: whether the exact-match rule produces false alarms once real document ids are used.

## Revisit when
A case study needs a different primary metric (for example answer-level grading), or exact-match entitlement proves too strict for real document ids.
