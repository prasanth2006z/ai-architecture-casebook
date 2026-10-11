# Research: Shared Evaluation Harness

No `NEEDS CLARIFICATION` items remained after the spec and the plan input. The decisions below close the open design points.

## R1. Plug-in mechanism

- **Decision**: a POC passes plain callables wrapped in a `Configuration(name, retrieve, answer=None)` dataclass. `retrieve(question_text, profile) -> list[RetrievalResult]`; `answer(question_text, profile, results) -> Answer`.
- **Rationale**: no framework dependency (as requested); trivially testable with lambdas; one object per compared configuration.
- **Alternatives**: abstract base class (more ceremony, no benefit); entry-point plugin registry (overkill).
- **Note**: `answer` receives the retrieval results already obtained for that question, so citation validity is checked against exactly those chunks and retrieval is not run twice.

## R2. Question file format

- **Decision**: JSONL, one JSON object per line, UTF-8. Blank lines ignored. Validation by hand-written code that reports file, line number, question id (if known) and field.
- **Rationale**: diffs cleanly in git; standard library `json`; avoids a validation dependency.
- **Alternatives**: JSON array (noisy diffs), YAML (needs a dependency), pydantic (dependency).

## R3. CLI loading of configurations

- **Decision**: `evals run --questions FILE --config SPEC [--config SPEC ...] --k 5 --out-dir DIR`, where `SPEC` is `module:attr` or `path/to/file.py:attr`. `attr` is either a `Configuration` or a zero-argument function returning one.
- **Rationale**: lets the author run the shipped sample and any POC without writing a driver script, while the library API stays the primary interface.
- **Alternatives**: config file listing configurations (extra format to maintain).

## R4. Percentile method

- **Decision**: nearest-rank percentile on the sorted list of successful-call latencies in milliseconds: value at index `ceil(p/100 * n) - 1`.
- **Rationale**: deterministic, no interpolation surprises, standard library, easy to explain in an article. With few questions p95 equals the max, and the README says so.
- **Alternatives**: `statistics.quantiles` (interpolated; differs by method argument).
- **Edge**: no successful calls gives "n/a".

## R5. Timing

- **Decision**: `time.perf_counter()` around each `retrieve` call only. Answer time is not part of the spec's latency metric and is not reported.
- **Rationale**: matches FR-008. Monotonic clock avoids wall-clock adjustments.

## R6. Determinism

- **Decision**: results are processed in question-file order; JSON written with sorted keys and fixed indentation; no timestamps or run ids in the results file; the table row order is the order configurations were given. Latency fields are the only values that differ between runs, and tests compare results with latency removed.
- **Rationale**: FR-015 and SC-004.

## R7. Entitlement matching (security-critical)

- **Decision**: exact, case-sensitive string equality between each returned result's document id and the entries on the question's not-entitled list, counted per returned result across **all** returned results (not only top k), regardless of rank or expected document. A result whose document id is missing, empty, or not text **fails closed**: it is counted as a cross-entitlement retrieval (entitlement cannot be verified) AND its question is recorded as an error (`stage: "validate"`). All other results of that question are still checked for entitlement, but the question scores as a miss for hit rate, section hit rate and MRR like any other error (see R8).
- **Rationale**: fail closed. Normalizing (case, whitespace) could hide a real cross-entitlement retrieval or invent a match; exact matching keeps the check auditable. Counting all returned results matters because a cross-entitlement retrieval at rank 20 is still one. An unverifiable result must never lower the cross-entitlement count.
- **Alternatives**: top-k only (understates the count); normalized matching (ambiguous); error only without counting (could hide a cross-entitlement retrieval, rejected by the author).
- **Decided by the author**: fail closed, count and error. The cross-entitlement count therefore means "results proven forbidden or not provably allowed".
- **Ownership**: the author writes `entitlement.py` (Principle VIII). Tasks provide the failing tests and a stub.
- **Record**: this rule must be stated in ADR-001 (see plan.md).

## R8. Error handling

- **Decision**: one rule for every error. A question is recorded as an error (`{stage, type, message}`, stage `retrieve`, `answer` or `validate`) when `retrieve` or `answer` raises, or a returned result has an unverifiable document id. Any errored question scores as a miss for hit rate, section hit rate and MRR (no hit, rank contribution 0), as not a correct refusal, not a refusal, and invalid citations, stays in all denominators, and is excluded from the latency percentiles. Harness bugs (e.g. in metrics) are not caught.
- **Entitlement exception**: errors never lower the cross-entitlement total. Results the function did return are still checked, and unverifiable ones count (R7). A `validate` error skips the `answer` call, since the retrieved results cannot be trusted.
- **Rationale**: FR-014a without hiding defects in the harness itself; a single rule keeps published numbers easy to explain.

## R9. Markdown table

- **Decision**: one row per configuration. Columns, in order: Configuration, Hit@k, Section hit@k, MRR, Cross-entitlement, Latency p50 (ms), Latency p95 (ms), Errors, then (only when an answer function exists) Correct refusal, False refusal, Citation validity. Rates show as percentages to one decimal with the count in the cell's raw form in the JSON; "n/a" where undefined. A footer line states k, question count, and question file name, followed by one notes line per "n/a" cell explaining why (for example "False refusal: n/a, no should-answer questions"). Section hit rate is "n/a" only when no result in the configuration carries a section; otherwise a result without a section never matches an expected section. When only some configurations have an answer function, the answer columns show "n/a" for the others.
- **Rationale**: pasteable into a README; primary metric first per FR-005a.

## R10. Dev tooling

- **Decision**: uv for environment and lock; pytest; ruff for lint and format; type hints throughout, checked by review (no separate type checker required by the constitution).
- **Rationale**: Principle VII.
