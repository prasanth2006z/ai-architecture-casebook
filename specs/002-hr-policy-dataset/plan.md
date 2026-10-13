# Implementation Plan: Synthetic HR Policy Dataset

**Branch**: `002-hr-policy-dataset` | **Date**: 2026-10-12 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-hr-policy-dataset/spec.md`

## Summary

A small, deterministic Python generator, package `hr_dataset`, in `01-permission-aware-rag/src/dataset/`. It renders about 51 synthetic HR policies from Markdown templates plus a value table per country and grade band (no LLM, no unseeded randomness), writes a `.metadata.json` sidecar per policy, and writes the 60-question JSONL file. The expected entitlement lists in the questions are computed from the metadata, never typed twice. A `validate` command checks every integrity rule in the spec, including loading the question file with the shared harness loader (`shared/evals`), and a `build --check` mode proves the committed files equal a fresh build. The entitlement rule (`is_entitled`, `not_entitled_for`) is isolated in its own module, marked security-critical, and left for the author to write (Principle VIII).

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: none at runtime (standard library only: `string.Template`, `tomllib`, `json`, `random`, `pathlib`, `argparse`)

**Dev Dependencies**: pytest, ruff, and the shared harness `evals` as an editable path dependency (`../../../shared/evals`), used only by the validate command and tests

**Tooling**: uv (project, lock file, run)

**Storage**: files only. Input: Markdown templates and TOML value/question tables. Output: Markdown policies, JSON sidecars, one JSONL file.

**Testing**: pytest. Spec acceptance criteria (SC-001 to SC-007) become automated tests (Principle IV).

**Target Platform**: any machine with Python 3.12 and uv (developed on Windows 11; must give byte-identical output on Linux/macOS)

**Project Type**: single uv project with a small CLI (`hr-dataset build | validate`)

**Performance Goals**: not a goal; a full build is well under a second.

**Constraints**: no network, no cloud SDK, no LLM. Output uses UTF-8, LF line endings, sorted keys and no timestamps, so reruns are byte-identical on any OS. Random choices (question order, wording variants) use one `random.Random(SEED)` with a constant seed.

**Scale/Scope**: ~51 documents, ~60 questions, 18 country topics plus restricted and global documents (see [data-model.md](data-model.md)).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | How the plan satisfies it |
|-----------|--------|---------------------------|
| I. Architecture Decisions First | Pass | The dataset exists to prove [ADR-002](../../01-permission-aware-rag/docs/adr/ADR-002-access-control-in-retrieval.md) (entitlement fields, metadata shape) and [ADR-003](../../01-permission-aware-rag/docs/adr/ADR-003-section-based-chunking.md) (numbered sections, split rule/condition). The package docstring and README link both. No new decision contradicts an ADR; the one extension (Bedrock sidecar wrapper plus extra fields) is recorded in [research.md](research.md) R3 and does not change ADR-002's fields. |
| II. Security by Construction | Pass | Entitlement ground truth comes only from document metadata and the asker profile, never from question text. Tests try to break it: a question whose expected document is restricted or other-country, a not-entitled list missing one document, a global document wrongly listed, a superseded expected document. |
| III. Synthetic Data Only | Pass | Every policy and every sidecar is labeled synthetic; "Globex Corp" is the only company name. A validator check scans for a banned-pattern list (email addresses, phone numbers, URLs, and a small denylist of real company names) and requires the label. |
| IV. Evaluation Is Mandatory | Pass | This feature produces the evaluation data. Its acceptance criteria become pytest tests plus the `validate` command. No quality claim without a check. |
| V. Cost Control | Pass (not applicable) | No cloud resources, so no Terraform or teardown. README states cost: none. |
| VI. Simplicity | Pass | Standard library only, plain dataclasses, `string.Template`, no templating engine. Value and question tables are small TOML files grouped by topic or category. |
| VII. Python Standards | Pass | Python 3.12, uv, pytest, type hints (ruff `ANN`), small functions, `pyproject.toml` with lock file. |
| VIII. Human Review (v1.0.1) | Gate for implementation | `hr_dataset/entitlement.py` is **security-critical** (it decides who may see which document, and its output is the scoring ground truth): the author writes it; tasks generate a failing test suite and a stub only. Template wording, value tables and question text are data that Claude may draft; the author reviews them. Everything else is covered by the author's normal review of every change. |
| IX. Reproducibility | Pass | README runs from a fresh clone in under 10 minutes; `build --check` and a double-build test enforce identical output. See [quickstart.md](quickstart.md). |

**Layout note**: the constitution puts code in `src/` and datasets in `evals/`. The uv project lives at `src/dataset/`; generated data is committed under `evals/` (see Project Structure). No violation, so Complexity Tracking is empty.

**Post-design re-check**: all principles still pass after Phase 1. The only tension, "standard library only at runtime" versus loading the shared harness in `validate`, is resolved by making `evals` a dev-group dependency (itself standard-library only); `build` never imports it.

## Project Structure

### Documentation (this feature)

```text
specs/002-hr-policy-dataset/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset-files.md     # policy Markdown, sidecar JSON, question file conventions
│   └── cli.md               # build / validate commands, exit codes, messages
├── checklists/requirements.md
└── tasks.md                 # /speckit-tasks, not created here
```

### Source Code

```text
01-permission-aware-rag/
├── src/dataset/                      # uv project root
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── README.md                     # run, validate, results (Principle IX)
│   ├── data/
│   │   ├── values/*.toml             # value tables by topic group: per topic, per country, per grade band
│   │   └── questions/*.toml          # question tables by category (text, asker, topic key, section); no entitlement lists
│   ├── templates/                    # one Markdown template per topic (string.Template)
│   │   ├── annual-leave.md
│   │   └── ...
│   ├── src/hr_dataset/
│   │   ├── __init__.py               # docstring links ADR-002, ADR-003
│   │   ├── models.py                 # Policy, Metadata, Question dataclasses
│   │   ├── catalog.py                # expands topics x countries (+ restricted, superseded, global) into Policy objects
│   │   ├── render.py                 # template + values -> Markdown text
│   │   ├── entitlement.py            # SECURITY-CRITICAL, author-written: is_entitled, not_entitled_for
│   │   ├── questions.py              # question table + metadata -> question records
│   │   ├── writer.py                 # deterministic file output (UTF-8, LF, sorted keys)
│   │   ├── validate.py               # integrity rules from the spec
│   │   └── cli.py                    # build, validate
│   └── tests/
│       ├── test_catalog.py
│       ├── test_render.py
│       ├── test_entitlement.py       # failing tests first, golden lists hand-checked
│       ├── test_questions.py
│       ├── test_validate.py
│       └── test_reproducible.py      # build twice, compare bytes
└── evals/
    ├── policies/                     # generated: <doc-id>.md and <doc-id>.md.metadata.json
    └── questions.jsonl               # generated: 60 questions
```

**Structure Decision**: one uv project at `src/dataset/` with a `src/hr_dataset/` package (mirrors `shared/evals`). Inputs (templates, TOML tables) sit beside the package and are the only hand-edited data; `evals/` holds generated output that is committed so POCs can use it without running the generator, and `validate`/`build --check` keeps it honest.

## Complexity Tracking

No violations to justify.
