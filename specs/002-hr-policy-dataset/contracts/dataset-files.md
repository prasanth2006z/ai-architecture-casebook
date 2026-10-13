# Contract: dataset files

All files are UTF-8 with LF line endings, no byte-order mark, ending with one newline. Synthetic content only (constitution Principle III).

## Layout

```text
01-permission-aware-rag/evals/
├── policies/
│   ├── parental-leave-uk.md
│   ├── parental-leave-uk.md.metadata.json
│   └── ...                       # ~51 pairs
└── questions.jsonl               # 60 lines
```

## Policy Markdown (`<document_id>.md`)

```markdown
> SYNTHETIC DATA: Globex Corp is a fictional company. This policy is invented for testing.

# Parental Leave Policy (United Kingdom)

Policy code: HR-PL-UK-001 · Version 2.0 · Effective 2026-04-01

## 1. Purpose
...

## 3. Entitlement
### 3.1 Leave entitlement
Eligible employees in the United Kingdom receive 26 weeks of parental leave.
### 3.2 Eligibility
The entitlement in 3.1 applies after 12 months of continuous service.
```

Rules:

- First line is the synthetic label (exact prefix `> SYNTHETIC DATA:`); second non-blank line is the single `# Title`.
- Sections use `## N. Title`; subsections use `### N.M Title`. Numbers are consecutive and unique. Section ids used in questions are `N` or `N.M`.
- Every document has at least four sections. Some documents hold an entitlement and its condition in separate subsections.
- The `Policy code`, version and effective date line matches the sidecar.
- Exactly one document (`remote-work-uk`, section 5) contains instruction-like text, labeled as a synthetic test probe.

## Sidecar (`<document_id>.md.metadata.json`)

```json
{
  "metadataAttributes": {
    "allowed_countries": ["UK"],
    "allowed_grades": ["G1-6", "G7+"],
    "document_id": "parental-leave-uk",
    "effective_date": "2026-04-01",
    "status": "current",
    "synthetic": true,
    "title": "Parental Leave Policy (United Kingdom)",
    "version": "2.0"
  }
}
```

Keys sorted, two-space indent. Field rules are in [data-model.md](../data-model.md).

## Question file (`questions.jsonl`)

Conforms to `specs/001-eval-harness/contracts/question-file.md`: required keys `id`, `question`, `profile` (`country`, `grade_band`), `should_refuse`, `not_entitled_documents`; optional `expected_document`, `expected_section`. No other keys (unknown keys are rejected). Keys are written in the order shown below; `not_entitled_documents` is sorted.

```json
{"id": "c03", "question": "How many weeks of parental leave do I get?", "profile": {"country": "IN", "grade_band": "G1-6"}, "expected_document": "parental-leave-in", "expected_section": "3.1", "should_refuse": false, "not_entitled_documents": ["annual-leave-uk", "exec-compensation-in", "..."]}
```

Additional conventions of this dataset:

- Category is the id prefix: `s` single-country, `c` country-differing, `o` out-of-scope, `p` entitlement probe; two-digit number.
- Refusals (`o01-o10`, `p04-p05`) have `should_refuse` true, `expected_document` null and `expected_section` null.
- The question text never names a document id or a section number.
- `not_entitled_documents` follows the rule in [data-model.md](../data-model.md) and is checked by `validate` against the sidecars.
