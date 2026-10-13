# Quickstart: Synthetic HR Policy Dataset

Validation guide for the finished generator. Cost: none (no cloud resources, nothing to tear down).

## Prerequisites

- Python 3.12 and [uv](https://docs.astral.sh/uv/)
- A fresh clone of the repository (the shared harness at `shared/evals` must be present)

## Setup

```text
cd 01-permission-aware-rag/src/dataset
uv sync
```

## Scenario 1: build and validate (SC-001 to SC-005)

```text
uv run hr-dataset build
uv run hr-dataset validate
```

Expected: `evals/policies/` holds 51 Markdown files with 51 sidecars, `evals/questions.jsonl` holds 60 lines, and every validate line starts with `PASS` (exit code 0). The last check confirms the shared harness loader accepts the question file. Details: [contracts/cli.md](contracts/cli.md).

## Scenario 2: reproducibility (SC-006)

```text
uv run hr-dataset build --check
uv run pytest tests/test_reproducible.py
```

Expected: exit code 0 and the test passes. Editing one value in a file under `data/values/` and rerunning `--check` must report the changed file and exit 1; restore the value afterwards.

## Scenario 3: failure conditions are present (SC-007)

Open these and confirm by eye:

- `evals/policies/parental-leave-uk.md` and `parental-leave-in.md`: near-identical, differing in numbers, country names and policy codes.
- `evals/policies/exec-relocation-uk.md.metadata.json`: `allowed_grades` is `["G7+"]`.
- `evals/policies/business-travel-uk-v1.md.metadata.json`: `status` is `superseded`.
- `evals/policies/remote-work-uk.md` section 5: the synthetic injection probe.
- A policy with entitlement in 3.1 and its condition in 3.2.

## Scenario 4: the checks catch mistakes

Temporarily edit one `not_entitled_documents` entry in `evals/questions.jsonl` and run `uv run hr-dataset validate`: expect a `FAIL` line naming the question, exit code 1. Rebuild to restore.

## Scenario 5: tests

```text
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

Expected: all pass. `tests/test_entitlement.py` fails until the author writes `entitlement.py` (Principle VIII).
