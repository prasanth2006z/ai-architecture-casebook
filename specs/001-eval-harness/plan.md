# Implementation Plan: Shared Evaluation Harness

**Branch**: `001-eval-harness` | **Date**: 2026-10-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-eval-harness/spec.md`

## Summary

A small, dependency-free Python package, `evals`, that every case study imports to score its POC. A POC passes plain callables (retrieval, and optionally answering) wrapped in named configurations. The harness loads a JSONL question set, runs each configuration over every question, computes the metrics in the spec, and writes a Markdown results table (stdout and file) plus a JSON file with per-question outcomes. A thin command-line entry point runs the same flow from the shell. The cross-entitlement check is isolated in its own module, marked security-critical, and left for the author to write (Principle VIII).

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: none at runtime (standard library only)

**Dev Dependencies**: pytest, ruff

**Tooling**: uv (project, lock file, run)

**Storage**: files only. Input is JSONL; output is Markdown and JSON.

**Testing**: pytest. Acceptance criteria from the spec become automated tests (Principle IV). Includes a 3-question sample set under `shared/evals/samples/`.

**Target Platform**: any machine with Python 3.12 and uv (developed on Windows 11, must also run on Linux/macOS)

**Project Type**: library with a small CLI

**Performance Goals**: not a goal. Harness overhead must be negligible next to the retrieval call being timed (a few hundred questions per configuration in seconds).

**Constraints**: no network or cloud SDK imports. Deterministic output apart from latency. Never crash on bad input; report it.

**Scale/Scope**: question sets of tens to low hundreds of questions, up to about five configurations per run.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | How the plan satisfies it |
|-----------|--------|---------------------------|
| I. Architecture Decisions First | Pass, with a deliverable | The harness is shared infrastructure, not a POC, but its metric definitions (document-level primary metric, error-as-miss, nearest-rank percentiles, JSONL) are decisions every case study depends on. They are recorded in `shared/evals/docs/adr/ADR-001-eval-metric-definitions.md` (task to create), which MUST state the fail-closed entitlement rule: a result with a missing or empty document id counts as a cross-entitlement retrieval and marks its question as an error, and that every errored question scores as a miss for hit rate, section hit rate and MRR without lowering the cross-entitlement total. Package docstring links to it. |
| II. Security by Construction | Pass | Entitlement check is built only from the question set's not-entitled list and the returned document ids, never from model output. Tests attempt to violate it (expected document that is also not-entitled; casing, whitespace, and missing, empty, or non-text document ids, which must count as cross-entitlement retrievals and as errors). |
| III. Synthetic Data Only | Pass | Sample questions and documents are synthetic and labeled as such. |
| IV. Evaluation Is Mandatory | Pass | This feature is the evaluation tool; its own acceptance criteria (SC-001 to SC-009) become pytest tests. No quality claim ships without a test. |
| V. Cost Control | Pass (not applicable) | No cloud resources, so no Terraform or teardown. README states cost: none. |
| VI. Simplicity | Pass | Standard library only, plain dataclasses, no plugin framework, no UI. |
| VII. Python Standards | Pass | Python 3.12, uv, pytest, type hints, small functions, ruff, `pyproject.toml` with a lock file. |
| VIII. Human Review (v1.0.1) | Gate for implementation | Two classes of code. `evals/entitlement.py` is **security-critical** (an entitlement check) and is written by the author; tasks generate a failing test suite and a stub only. `evals/metrics.py` is **evaluation-core** (metric calculations): Claude may draft it, and the author reviews it line by line and rewrites any part they cannot explain (`[REVIEW]` tasks plus the final review gate). `runner.py`, `report.py` and the rest need no marker beyond the author's normal review of every change. |
| IX. Reproducibility | Pass | README runs from a fresh clone in under 10 minutes using the committed sample set; see [quickstart.md](quickstart.md). |

**Layout note**: the constitution's per-case-study layout does not apply to `shared/`. This plan places the uv project at `shared/evals/` with its own `src/`, `tests/`, `samples/` and `docs/adr/`. No violation, so Complexity Tracking is empty.

**Post-design re-check**: all principles still pass. No new violations from the design in Phase 1.

## Project Structure

### Documentation (this feature)

```text
specs/001-eval-harness/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── plugin-api.md
│   ├── question-file.md
│   ├── results-file.md
│   └── cli.md
├── checklists/requirements.md
└── tasks.md             # created later by /speckit-tasks
```

### Source Code (repository root)

```text
shared/evals/
├── pyproject.toml            # uv project, Python 3.12, pytest + ruff dev deps
├── uv.lock
├── README.md                 # run, evaluate, results (no teardown needed)
├── docs/adr/ADR-001-eval-metric-definitions.md
├── src/evals/
│   ├── __init__.py           # public API: Configuration, run_evaluation, ...
│   ├── models.py             # Question, UserProfile, RetrievalResult, Answer, outcomes
│   ├── questions.py          # JSONL loading and validation, clear errors
│   ├── runner.py             # runs configurations over questions, times calls, captures errors
│   ├── entitlement.py        # SECURITY-CRITICAL: cross-entitlement counting (author-written)
│   ├── metrics.py            # hit@k, section hit@k, MRR, refusal, citation, percentiles
│   ├── report.py             # Markdown table and JSON results file
│   └── cli.py                # argparse entry point: `evals`
├── samples/
│   ├── README.md             # states that all sample data is synthetic
│   ├── questions.jsonl       # 3 synthetic questions
│   ├── sample_configs.py     # stand-in retrieval and answer functions
│   └── expected_table.md     # committed sample table (latency masked in tests)
└── tests/
    ├── test_questions.py
    ├── test_entitlement.py   # security tests that try to violate the check
    ├── test_metrics.py
    ├── test_runner.py
    ├── test_runner_entitlement.py
    ├── test_compare.py
    ├── test_answers.py
    ├── test_sections_and_errors.py
    ├── test_report.py
    ├── test_cli.py
    ├── test_sample_end_to_end.py
    ├── test_expected_table.py
    └── test_no_network.py
```

**Structure Decision**: one uv project at `shared/evals/` with a `src/` layout. It is the simplest shape that gives an importable package for POCs and a console script. Each POC adds `evals` as a path dependency.

## Complexity Tracking

No constitution violations to justify.
