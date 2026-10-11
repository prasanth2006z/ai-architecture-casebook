# Contract: results file (JSON)

Written with sorted keys and two-space indentation. No timestamps. Identical inputs give identical files except the `latency_ms` values and the latency summary fields.

```json
{
  "k": 5,
  "question_file": "questions.jsonl",
  "question_count": 3,
  "configurations": [
    {
      "name": "semantic",
      "summary": {
        "hit_rate": {"value": 0.667, "numerator": 2, "denominator": 3},
        "section_hit_rate": {"value": null, "numerator": 0, "denominator": 0},
        "mrr": {"value": 0.5, "numerator": 1.5, "denominator": 3},
        "cross_entitlement_total": 0,
        "latency_p50_ms": 1.2,
        "latency_p95_ms": 3.4,
        "error_count": 0,
        "correct_refusal_rate": {"value": null, "numerator": 0, "denominator": 0},
        "false_refusal_rate": {"value": null, "numerator": 0, "denominator": 0},
        "citation_validity": {"value": null, "numerator": 0, "denominator": 0}
      },
      "outcomes": [
        {
          "question_id": "q1",
          "results": [{"document_id": "leave-policy-de", "chunk_id": "c1", "score": 0.91, "section": "parental-leave"}],
          "document_hit": true,
          "section_hit": true,
          "reciprocal_rank": 1.0,
          "cross_entitlement_count": 0,
          "latency_ms": 1.2,
          "refused": null,
          "refusal_correct": null,
          "false_refusal": null,
          "citations_valid": null,
          "error": null
        }
      ]
    }
  ]
}
```

`value` is `null` when `denominator` is 0 (shown as "n/a" in the Markdown table).

`error`, when present, is `{"stage": "retrieve" | "answer" | "validate", "type": "...", "message": "..."}`. Stage `validate` means a returned result had a missing or empty document id; such results are included in `cross_entitlement_count`. Any outcome with an `error` has `document_hit` false, `section_hit` false (when it has an expected section), `reciprocal_rank` 0 (when it has an expected document), and `latency_ms` null.
