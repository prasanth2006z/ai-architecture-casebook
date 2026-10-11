# Contract: question file (JSONL)

UTF-8, one JSON object per line, blank lines ignored. Synthetic content only.

```json
{"id": "q1", "question": "How many days of parental leave do I get?", "profile": {"country": "DE", "grade_band": "L3"}, "expected_document": "leave-policy-de", "expected_section": "parental-leave", "should_refuse": false, "not_entitled_documents": ["exec-comp-policy"]}
```

## Rules

- Required keys: `id`, `question`, `profile` (with `country`, `grade_band`), `should_refuse`, `not_entitled_documents`.
- Optional keys: `expected_document`, `expected_section` (both may be null or absent).
- `expected_document` may be null only when `should_refuse` is true.
- `id` values are unique. Unknown keys are rejected so typos are caught.

## Errors

Any problem stops the run before evaluation with a `QuestionFileError` whose message names the file, line number, question id (when readable) and field, for example:

`samples/questions.jsonl:2 (id "q2"): field "profile.country" is required`

Cases covered: file not found, unreadable, empty, invalid JSON on a line, missing field, wrong type, duplicate id, unknown key, null expected document on a non-refusal question.
