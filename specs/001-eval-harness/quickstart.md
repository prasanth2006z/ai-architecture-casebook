# Quickstart: Shared Evaluation Harness

Validation guide for the finished harness. Cost: none (no cloud resources, nothing to tear down).

## Prerequisites

- Python 3.12 and [uv](https://docs.astral.sh/uv/)
- A fresh clone of the repository

## Setup

```text
cd shared/evals
uv sync
```

## Scenario 1: run the sample end to end (SC-001, SC-002)

```text
uv run evals run --questions samples/questions.jsonl \
  --config samples/sample_configs.py:semantic \
  --config samples/sample_configs.py:hybrid
```

Expected: a Markdown table with two rows (see [cli.md](contracts/cli.md)), and `eval-results/results.md` and `eval-results/results.json` written. Exit code 0.

## Scenario 2: determinism (SC-004)

Run Scenario 1 twice into different `--out-dir` folders and compare the JSON files ignoring latency fields. They must match.

## Scenario 3: bad input (SC-005)

Edit a copy of the sample question file to remove `profile.country`, then run it. Expected: exit code 2 and a one-line message naming the file, line, question id and field. See [question-file.md](contracts/question-file.md).

## Scenario 4: tests (SC-003, SC-008, SC-009)

```text
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Expected: all tests pass, including the entitlement tests that try to violate the check.

## Using it from a POC

Build a `Configuration` from your retrieval function (and optionally your answer function) and call `run_evaluation`. See [plugin-api.md](contracts/plugin-api.md) and [data-model.md](data-model.md).
