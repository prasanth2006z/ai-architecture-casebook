# Data Model: Shared Evaluation Harness

All types are immutable dataclasses in `evals/models.py`. Field names match the JSON files.

## Question (input)

| Field | Type | Rules |
|-------|------|-------|
| `id` | string | required, non-empty, unique within the file |
| `question` | string | required, non-empty |
| `profile` | UserProfile | required |
| `expected_document` | string or null | null allowed only when `should_refuse` is true |
| `expected_section` | string or null | optional; null excludes the question from section hit rate |
| `should_refuse` | boolean | required |
| `not_entitled_documents` | list of strings | required, may be empty |

## UserProfile

| Field | Type | Rules |
|-------|------|-------|
| `country` | string | required, non-empty |
| `grade_band` | string | required, non-empty |

## RetrievalResult (returned by the POC)

| Field | Type | Rules |
|-------|------|-------|
| `document_id` | string | required and non-empty; a missing, empty, or non-string value fails closed: the result counts as a cross-entitlement retrieval and the question is recorded as an error |
| `chunk_id` | string | required |
| `score` | number | required |
| `section` | string or null | optional |

## Answer (returned by the POC, optional)

| Field | Type | Rules |
|-------|------|-------|
| `text` | string | may be empty when refused |
| `cited_chunk_ids` | list of strings | may be empty |
| `refused` | boolean | required |

## Configuration (supplied by the POC)

| Field | Type |
|-------|------|
| `name` | string, unique within a run |
| `retrieve` | callable `(str, UserProfile) -> list[RetrievalResult]` |
| `answer` | optional callable `(str, UserProfile, list[RetrievalResult]) -> Answer` |

## QuestionOutcome (per question, per configuration)

| Field | Type | Notes |
|-------|------|-------|
| `question_id` | string | |
| `configuration` | string | |
| `results` | list of RetrievalResult | as returned, in order; empty when the callable raised; kept in full when a result had an unverifiable document id |
| `document_hit` | boolean or null | expected document in top k; false for any errored question; null when the question has no expected document (excluded from the rate) |
| `section_hit` | boolean or null | false for any errored question that has an expected section; null when no expected section; false when the question has an expected section but no returned result matches it, including when results carry no section |
| `reciprocal_rank` | number or null | 0 for any errored question that has an expected document; null when no expected document |
| `cross_entitlement_count` | integer | across all returned results; includes results with an unverifiable document id |
| `latency_ms` | number or null | null for any errored question (excluded from percentiles) |
| `refused` | boolean or null | null without an answer function or for an errored question |
| `refusal_correct` | boolean or null | for should-refuse questions only; false when errored |
| `false_refusal` | boolean or null | for should-answer questions only; false when errored |
| `citations_valid` | boolean or null | null without an answer function; false when errored |
| `error` | `{stage, type, message}` or null | stage is `retrieve`, `answer`, or `validate` (unverifiable result) |

## ConfigurationSummary (per configuration)

`hit_rate`, `section_hit_rate`, `mrr`, `cross_entitlement_total`, `latency_p50_ms`, `latency_p95_ms`, `error_count`, `correct_refusal_rate`, `false_refusal_rate`, `citation_validity`, each with its numerator and denominator. A rate whose denominator is 0 is `null` in JSON and "n/a" in the table.

## Relationships

A run takes one question file and N configurations, producing N × (question count) outcomes and N summaries. Summaries are derived only from outcomes.
