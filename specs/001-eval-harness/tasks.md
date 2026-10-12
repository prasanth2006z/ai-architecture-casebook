---

description: "Task list for the shared evaluation harness"
---

# Tasks: Shared Evaluation Harness

**Input**: Design documents from `/specs/001-eval-harness/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included. Constitution Principle IV requires acceptance criteria to become automated tests, so each story writes its tests first and they must fail before implementation.

**Organization**: Tasks are grouped by user story. All paths are relative to the repository root; the harness is a uv project at `shared/evals/`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an unfinished task)
- **[Story]**: the user story from spec.md (US1 to US6)

## Principle VIII markers

- **[AUTHOR]**: security-critical code written or rewritten by the repository author. Claude MUST NOT implement these tasks; it may only prepare the stub and the failing tests that precede them.
- **[REVIEW]**: evaluation-core code that Claude may draft but the author reviews line by line before it is accepted.

## Path Conventions

- Source: `shared/evals/src/evals/`
- Tests: `shared/evals/tests/`
- Samples: `shared/evals/samples/`
- Docs: `shared/evals/docs/adr/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: project initialization

- [X] T001 Create the uv project in `shared/evals/pyproject.toml`: name `evals`, `requires-python = ">=3.12"`, `src` layout, no runtime dependencies, dev dependencies `pytest` and `ruff`, and a console script `evals = "evals.cli:main"`. Run `uv sync` in `shared/evals/` to produce `uv.lock`, and remove `shared/evals/.gitkeep`.
- [X] T002 Configure ruff and pytest in `shared/evals/pyproject.toml`: ruff lint and format with a line length of 100 and rules that require type hints on all functions (Principle VII); pytest `testpaths = ["tests"]`.
- [X] T003 Create the package skeleton: empty `shared/evals/src/evals/__init__.py`, plus the folders `shared/evals/tests/`, `shared/evals/samples/` and `shared/evals/docs/adr/`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: decisions, data types, question loading, and the security-critical entitlement check. No user story can start before this phase completes.

**⚠️ CRITICAL**: T010 is author-written. User story work that runs the harness (Phase 3 onward) cannot pass its tests until T010 is done.

- [X] T004 [REVIEW] Draft `shared/evals/docs/adr/ADR-001-eval-metric-definitions.md` from `templates/adr-template.md` (Principle I). Claude drafts the ADR; the author rewrites the Context and Alternatives sections before it is accepted, so Claude's text in those two sections is a placeholder only. It MUST record: JSONL question files; plain-callable plug-in API; document-level hit rate as the primary metric with section hit rate secondary; nearest-rank percentiles (research R4); the unified error rule (any errored question is a miss for hit rate, section hit rate and MRR, stays in denominators, and never lowers the cross-entitlement total); and the **fail-closed entitlement rule** (a result with a missing, empty or non-text document id counts as a cross-entitlement retrieval and marks its question as an error). Link it from the `evals` package docstring in `shared/evals/src/evals/__init__.py` (depends on T003; T020 later edits the same file).
- [X] T005 [P] Implement the immutable dataclasses in `shared/evals/src/evals/models.py` per `data-model.md`: `UserProfile`, `Question`, `RetrievalResult`, `Answer`, `Configuration`, `QuestionOutcome`, `ConfigurationSummary` (with value, numerator, denominator rates) and `EvaluationRun`. Keep the constraints in docstrings verbatim: `id` "required, non-empty, unique within the file"; `expected_document` "null allowed only when `should_refuse` is true"; `document_id` "required and non-empty; a missing, empty, or non-string value fails closed: the result counts as a cross-entitlement retrieval and the question is recorded as an error"; error stage is one of `retrieve`, `answer`, `validate`.
- [X] T006 [P] Write failing tests in `shared/evals/tests/test_questions.py` for every case in `contracts/question-file.md`: a valid file loads; blank lines are ignored; file not found, unreadable, empty file, invalid JSON on a line, missing field, wrong type, duplicate `id`, unknown key, and null `expected_document` on a non-refusal question each raise `QuestionFileError` whose message names the file, line number, question id (when readable) and field. All sample content is synthetic.
- [X] T007 Implement `load_questions` and `QuestionFileError` in `shared/evals/src/evals/questions.py` using only the standard library, so the tests in T006 pass (depends on T005, T006).
- [X] T008 Create the stub `shared/evals/src/evals/entitlement.py` marked `SECURITY-CRITICAL: author-written (Principle VIII)` in the module docstring. Define the frozen dataclass `EntitlementCheck(cross_entitlement_count: int, unverifiable_count: int)` and `check_entitlements(results, not_entitled_documents) -> EntitlementCheck` whose body raises `NotImplementedError`. Do not implement the logic (depends on T005).
- [X] T009 [P] Write failing security tests in `shared/evals/tests/test_entitlement.py` that try to violate the check (Principle II), against the T008 signature: a forbidden document at rank 1 counts; a forbidden document at rank 20 (beyond any k) counts; a forbidden document that is also the expected document counts; matching is exact and case-sensitive (`"Doc-A"` does not match `"doc-a"`, and whitespace is not trimmed); two forbidden results count as 2; no forbidden results gives 0; a result with a missing, empty or non-text `document_id` counts as a cross-entitlement retrieval AND increments `unverifiable_count`; other results in the same list are still checked; the input lists are not mutated (depends on T008).
- [X] T010 [AUTHOR] Implement `check_entitlements` in `shared/evals/src/evals/entitlement.py` so every test in T009 passes. **Written or rewritten by the repository author; Claude must not generate this implementation** (Principle VIII). Follows research R7: exact matching, all returned results, fail closed (depends on T009).

**Checkpoint**: models, question loading and the entitlement check are done; user stories can begin.

---

## Phase 3: User Story 1 - Evaluate one configuration and get a results table (Priority: P1) 🎯 MVP

**Goal**: from a question file and one retrieval function, produce a Markdown table and a JSON results file with hit rate, MRR, cross-entitlement total, error count and latency p50/p95.

**Independent Test**: run the 3-question sample with a stand-in retrieval function and confirm a table plus `results.md` and `results.json` are produced (SC-001, SC-002, SC-004).

### Tests for User Story 1 (write first, confirm they fail)

- [X] T011 [P] [US1] Write failing tests in `shared/evals/tests/test_metrics.py` for hit rate at k (expected document in top k; fewer results than k means no padding; empty result list is a miss), MRR@k (first result from the expected document within the top k, 0 when absent or ranked below k), section hit rate at k (a hit needs a result in the top k matching both the expected document and the expected section; a question without an expected section is excluded; a result without a section never matches an expected section, so such a question is a section miss and stays in the denominator; the rate is `value: null` only when no result in the configuration carries a section), questions without an expected document excluded from hit rate, section hit rate and MRR, rates reported as `value: null` with denominator 0, and nearest-rank percentiles (integer-arithmetic index `ceil(p * n / 100) - 1`; n=1; p95 equals the maximum for small n; no latencies gives n/a).
- [X] T012 [P] [US1] Write failing tests in `shared/evals/tests/test_runner.py`: `retrieve` is called exactly once per question per configuration in file order; outcomes carry the returned results in order; latency is recorded for each call; `run_evaluation` raises `ValueError` for `k < 1`, an empty question list, or an empty configuration list; two runs on the same inputs give identical outcomes once `latency_ms` is removed (FR-015).
- [X] T013 [P] [US1] Write failing tests in `shared/evals/tests/test_report.py`: the Markdown table has the columns in order Configuration, Hit@k, Section hit@k, MRR@k, Cross-entitlement, Latency p50 (ms), Latency p95 (ms), Errors; "n/a" is shown where undefined, with one notes line below the table per "n/a" cell explaining why (for example "False refusal: n/a, no should-answer questions"); a footer states k, question count and question file name; the JSON uses sorted keys, two-space indentation and no timestamps, and matches `contracts/results-file.md`.
- [X] T014 [P] [US1] Write failing tests in `shared/evals/tests/test_cli.py` and `shared/evals/tests/test_sample_end_to_end.py`: `evals run` on the sample prints the table to stdout, writes `results.md` and `results.json` to `--out-dir`, and exits 0; a malformed question file or an unloadable `--config` exits 2 with a one-line message on stderr and no traceback; both `module:attr` and `path/to/file.py:attr` config specs load; the run makes no network call.

### Implementation for User Story 1

- [X] T015 [P] [US1] Create the synthetic sample set `shared/evals/samples/questions.jsonl` with 3 synthetic questions (labeled by T015a) per `contracts/question-file.md`: one answerable question with an expected document and section, one answerable question with an expected document and no section, and one `should_refuse` question with a null expected document. Give each a non-empty `not_entitled_documents` list.
- [X] T015a [P] [US1] Create `shared/evals/samples/README.md` stating that all sample data (questions, documents, results) is synthetic and contains no real company, customer or personal data (Principle III). The question-file contract stays strict: unknown keys are still rejected, so no label field is added to the JSONL.
- [X] T016 [P] [US1] Create `shared/evals/samples/sample_configs.py` with two deterministic stand-in retrieval-only configurations, `semantic` and `hybrid`, built as `Configuration` objects from plain functions with hard-coded synthetic results.
- [X] T017 [US1] [REVIEW] Implement in `shared/evals/src/evals/metrics.py`: hit rate at k, section hit rate at k (with the missing-section rule from T011), mean reciprocal rank, nearest-rank percentile, and the rate helper returning value, numerator and denominator (null value when the denominator is 0), so the T011 tests pass.
- [X] T018 [US1] Implement `run_evaluation` in `shared/evals/src/evals/runner.py`: validate arguments (T012 cases), call each configuration's `retrieve` once per question in file order timed with `time.perf_counter()`, call `check_entitlements` from `entitlement.py` for every question, build `QuestionOutcome` and `ConfigurationSummary` using `metrics.py`, and return an `EvaluationRun` (depends on T010, T017).
- [X] T019 [US1] Implement `render_markdown` and `write_results_json` in `shared/evals/src/evals/report.py` per research R9 and `contracts/results-file.md`, including the notes line for each "n/a" cell (depends on T018).
- [X] T020 [US1] Implement the command line in `shared/evals/src/evals/cli.py` per `contracts/cli.md` (`evals run --questions --config [--config ...] [--k] [--out-dir]`, `module:attr` or `file.py:attr` specs, exit codes 0 and 2) and export the public API (`Configuration`, `run_evaluation`, `load_questions`, `render_markdown`, `write_results_json`) from `shared/evals/src/evals/__init__.py` (depends on T019).

**Checkpoint**: User Story 1 works end to end and is independently testable.

---

## Phase 4: User Story 2 - Catch cross-entitlement retrievals (Priority: P1)

**Goal**: the cross-entitlement total reaches the table and results file correctly through a full run, including the fail-closed case.

**Independent Test**: a question whose expected document is also forbidden, returned by a retrieval function, appears in the cross-entitlement column; a result with an empty document id is counted and its question shows as an error miss (SC-003).

### Tests for User Story 2 (write first, confirm they fail)

- [X] T021 [P] [US2] Write failing run-level tests in `shared/evals/tests/test_runner_entitlement.py`: a forbidden document returned adds 1 per result to `cross_entitlement_count` and to the configuration total in the table; a forbidden document that is also the expected document is still counted; no forbidden results shows 0 in the table; a result with a missing, empty or non-text `document_id` is included in `cross_entitlement_count`, the question has `error.stage == "validate"`, `document_hit` is false, `section_hit` is false when an expected section exists, `reciprocal_rank` is 0, `latency_ms` is null, and the question stays in all denominators.

### Implementation for User Story 2

- [X] T022 [US2] Wire the fail-closed path into `shared/evals/src/evals/runner.py`: when `EntitlementCheck.unverifiable_count > 0`, record an error with stage `validate`, score the question as a miss for hit rate, section hit rate and MRR, null its latency, and still add all counted results to the total, per FR-007 and FR-014a (depends on T018, T021).

**Checkpoint**: User Stories 1 and 2 both work; the cross-entitlement count is proven through the runner.

---

## Phase 5: User Story 3 - Compare configurations side by side (Priority: P2)

**Goal**: several configurations of one POC appear as rows of a single table, computed on the same questions.

**Independent Test**: three configurations produce a three-row table and a results file whose outcomes are labeled by configuration (SC-007).

### Tests for User Story 3 (write first, confirm they fail)

- [ ] T023 [P] [US3] Write failing tests in `shared/evals/tests/test_compare.py`: three configurations give three table rows in the order supplied, with identical columns; every outcome in the JSON has its configuration name; duplicate configuration names raise `ValueError`; all configurations see the same questions in the same order.

### Implementation for User Story 3

- [ ] T024 [US3] Add the duplicate-name check and configuration-order guarantees to `run_evaluation` in `shared/evals/src/evals/runner.py`, and make `render_markdown` in `shared/evals/src/evals/report.py` emit one row per configuration (depends on T022, T023).
- [ ] T025 [P] [US3] Add a third stand-in configuration, `hybrid_rerank`, to `shared/evals/samples/sample_configs.py` so the sample supports a three-way comparison.

**Checkpoint**: Stories 1 to 3 work independently.

---

## Phase 6: User Story 4 - Measure answers: refusals and citations (Priority: P2)

**Goal**: with an answer function, report correct-refusal rate, false-refusal rate and citation validity; without one, show them as n/a.

**Independent Test**: the sample with an answer function shows the three answer metrics; the same sample without one shows n/a and still reports retrieval metrics.

### Tests for User Story 4 (write first, confirm they fail)

- [ ] T026 [P] [US4] Write failing tests in `shared/evals/tests/test_answers.py`: correct-refusal rate uses should-refuse questions as its denominator and false-refusal rate uses all other questions; each is "n/a" when its denominator is 0; an answer citing a chunk not among that question's retrieved results has invalid citations, including a chunk id that appears only in a different question's results; `answer` receives the same results `retrieve` returned and retrieval is not run twice; without an answer function the answer columns are absent from the table and the metrics are n/a; when only some configurations have an answer function, the columns appear and the others show "n/a"; after a `validate` error (a result with a missing or empty document id) the `answer` function is never called for that question.

### Implementation for User Story 4

- [ ] T027 [US4] [REVIEW] Add correct-refusal rate, false-refusal rate and citation validity to `shared/evals/src/evals/metrics.py` (depends on T017, T026).
- [ ] T028 [US4] Call the optional `answer` function in `shared/evals/src/evals/runner.py` with the question, profile and retrieved results, and record `refused`, `refusal_correct`, `false_refusal` and `citations_valid` on each outcome. Skip the call when the question has a `validate` error (an unverifiable result) (depends on T022, T027).
- [ ] T029 [US4] In `shared/evals/src/evals/report.py`, add the Correct refusal, False refusal and Citation validity columns when at least one configuration has an answer function, showing "n/a" for configurations without one (depends on T028).
- [ ] T030 [P] [US4] Add a deterministic stand-in answer function to the `hybrid` configuration in `shared/evals/samples/sample_configs.py`, so the sample refuses the should-refuse question and cites retrieved chunks.

**Checkpoint**: Stories 1 to 4 work independently.

---

## Phase 7: User Story 5 - Score section-level retrieval and surface failures (Priority: P2)

**Goal**: verify the section-level edge cases and treat any errored question under one consistent rule, with an error count per configuration. The section hit rate computation itself is built in User Story 1 (T011, T017).

**Independent Test**: a set with one section hit, one document-hit/section-miss, one question without a section and one failing retrieval call gives the section hit rate, the miss and the error count described in the spec (SC-008).

### Tests for User Story 5 (write first, confirm they fail)

- [ ] T031 [P] [US5] Write failing tests in `shared/evals/tests/test_sections_and_errors.py`: edge cases on top of the section metric from T017: expected document under another section is a document hit and a section miss; a question without an expected section is excluded from section hit rate only; a question with an expected section whose results carry no section is a section miss and stays in the denominator; section hit rate is "n/a" only when no result in the configuration carries a section; when `retrieve` raises, the run continues, the error (`stage: "retrieve"`, type, message) is recorded, the question is a miss for hit rate, section hit rate and MRR, it adds 0 to the cross-entitlement total, and it is excluded from the latency percentiles; the same holds when `answer` raises (`stage: "answer"`) plus not a correct refusal, not a refusal and invalid citations; the Errors column equals the number of errored questions; errored questions stay in every denominator.

### Implementation for User Story 5

- [ ] T032 [US5] [REVIEW] Make `shared/evals/src/evals/metrics.py` aggregate errored outcomes per FR-014a: an errored question stays in every denominator it would otherwise belong to as a miss (hit rate, section hit rate, MRR 0), counts as failed for the answer metrics, and is excluded from the latency percentiles; add the per-configuration error count (depends on T027, T031).
- [ ] T033 [US5] In `shared/evals/src/evals/runner.py`, catch exceptions from `retrieve` and `answer` per question, record `{stage, type, message}`, and apply the single error rule from FR-014a to every errored question including the `validate` stage from T022 (miss for hit rate, section hit rate and MRR; failed for the answer metrics; null latency; stays in denominators; never lowers the cross-entitlement total). Harness bugs outside the two callables must not be caught (depends on T028, T032).

**Checkpoint**: Stories 1 to 5 work independently; error handling is uniform.

---

## Phase 8: User Story 6 - Reproduce results from a fresh clone (Priority: P3)

**Goal**: a reader on a clean checkout reproduces the published sample table in under 10 minutes.

**Independent Test**: follow the README on a clean checkout and match the committed sample table except for latency values (SC-006).

- [ ] T034 [US6] Write `shared/evals/README.md` (Principle IX): prerequisites (Python 3.12, uv), setup (`uv sync`), run the sample (`uv run evals run ...`), run the tests, how a POC builds a `Configuration` (link `specs/001-eval-harness/contracts/plugin-api.md`), what each output file contains, a note that p95 equals the maximum for small question sets, expected cost (none, no cloud resources, nothing to tear down), and a link to ADR-001.
- [ ] T035 [US6] Commit the expected sample table as `shared/evals/samples/expected_table.md` and add `shared/evals/tests/test_expected_table.py`, which runs the sample and compares it with the committed table with the latency columns masked (depends on T034).

---

## Phase 9: Polish & Cross-Cutting Concerns

- [ ] T036 [P] Add `shared/evals/tests/test_no_network.py` asserting that no module under `shared/evals/src/evals/` imports a third-party or networking package (standard library only; FR-016).
- [ ] T037 Run `uv run ruff check .` and `uv run ruff format --check .` in `shared/evals/` and fix every finding (Principle VII).
- [ ] T038 Run every scenario in `specs/001-eval-harness/quickstart.md` from a fresh `uv sync`, time the run from `uv sync` to the printed table (SC-006: under 10 minutes), and confirm the expected outcomes, including exit code 2 on a question file missing `profile.country`.
- [ ] T039 [AUTHOR] Author review gate (Principle VIII): the repository author reads `shared/evals/src/evals/entitlement.py` and `shared/evals/src/evals/metrics.py` line by line against ADR-001 and research R4 and R7, then records the sign-off in the commit message or pull request. Nothing is accepted before this is done.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: depends on Setup. T010 is author-written and blocks every run-level test from passing.
- **User stories (Phases 3 to 8)**: depend on Foundational. US1 and US2 are both P1; US2 builds on the US1 runner.
- **Polish (Phase 9)**: depends on the stories you want shipped.

### User Story Dependencies

- **US1 (P1)**: starts after Foundational (including T010). MVP. It includes the section hit rate computation.
- **US2 (P1)**: needs the US1 runner (T018). Independently testable through its own tests.
- **US3 (P2)**: needs the US2 runner changes in the same file.
- **US4 (P2)**: needs T017 and the runner; independent of US3 behavior.
- **US5 (P2)**: needs US4 for the answer-error cases (T033 after T028).
- **US6 (P3)**: needs US1 for the sample run; the final committed table should be taken after US4 so it includes the answer columns.

### Within Each Story

- Tests first, and confirm they fail.
- `models.py` before `metrics.py`, `metrics.py` before `runner.py`, `runner.py` before `report.py`, `report.py` before `cli.py`.
- `metrics.py` (T017, T027, T032) and `runner.py` (T018, T022, T024, T028, T033) are edited in several stories, so those tasks run in sequence, never in parallel. `shared/evals/src/evals/__init__.py` is edited by T004 and T020, also in sequence. Task ID T015a was inserted to avoid renumbering.

### Parallel Opportunities

- Foundational: T005 and T006 together; T009 can be written in parallel with T007 once T008 exists.
- US1 tests T011 to T014 and samples T015 and T016 together.
- Each story's test-writing task can run in parallel with sample-file tasks for the same story.
- Different stories' test files (T021, T023, T026, T031) can be written in parallel because they are separate files.

---

## Parallel Example: User Story 1

```text
# Launch all US1 tests together:
Task: "Write failing tests in shared/evals/tests/test_metrics.py"
Task: "Write failing tests in shared/evals/tests/test_runner.py"
Task: "Write failing tests in shared/evals/tests/test_report.py"
Task: "Write failing tests in shared/evals/tests/test_cli.py and test_sample_end_to_end.py"

# Alongside them, the sample files:
Task: "Create shared/evals/samples/questions.jsonl"
Task: "Create shared/evals/samples/sample_configs.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup.
2. Phase 2: Foundational, including your own T010 (entitlement check).
3. Phase 3: User Story 1.
4. **Stop and validate**: run the sample and compare the table with quickstart Scenario 1.

### Incremental Delivery

1. Setup and Foundational, then US1 (MVP).
2. US2 proves the cross-entitlement count through the runner (P1, do this before any case study relies on the numbers).
3. US3 comparison, US4 answers, US5 sections and error handling, in that order.
4. US6 README and reproducibility, then Polish and the T039 review gate.

---

## Notes

- Tasks marked [AUTHOR] are not to be implemented by Claude; Claude prepares the stub (T008) and the failing tests (T009) only.
- Verify tests fail before implementing; commit after each task or logical group.
- All sample data is synthetic and labeled as such (Principle III).
