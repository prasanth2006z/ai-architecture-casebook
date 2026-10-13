# Contract: command line

Entry point `hr-dataset`, run from `01-permission-aware-rag/src/dataset/` with `uv run hr-dataset ...`.

## `hr-dataset build [--out DIR] [--check]`

Renders every policy, sidecar and the question file.

| Option | Default | Meaning |
|--------|---------|---------|
| `--out DIR` | `../../evals` (resolved from the project folder) | Folder that receives `policies/` and `questions.jsonl` |
| `--check` | off | Build in memory and compare byte for byte with the files in `--out`; write nothing |

- Build writes files only inside `--out`; stale files in `policies/` that the catalog no longer produces are removed.
- Exit codes: `0` success (or `--check` identical); `1` `--check` found differences (lists each differing path); `2` input problem (missing template value, bad table), with a message naming the topic, country and placeholder.

## `hr-dataset validate [--data DIR]`

Runs all integrity rules against the generated files in `--data` (default as above) and prints one line per check.

```text
PASS  every document has a sidecar and vice versa (51 documents)
PASS  60 questions: s=30 c=15 o=10 p=5
PASS  question file loads with the shared harness loader
FAIL  p02: expected document "exec-travel-uk" is not entitled for UK G1-6
```

- Checks are listed in [research.md](../research.md) R8. All checks run even after a failure.
- The last check calls the shared harness question-file loader; a `QuestionFileError` message is shown unchanged.
- Exit codes: `0` all pass; `1` one or more checks failed (summary line `N checks failed`); `2` the data folder is missing or unreadable.

## Not provided

No network access, no cloud calls, no model calls, no retrieval. Output is identical for identical inputs.
