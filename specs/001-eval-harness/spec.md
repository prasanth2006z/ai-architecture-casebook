# Feature Specification: Shared Evaluation Harness

**Feature Branch**: `001-eval-harness`

**Created**: 2026-10-11

**Status**: Draft

**Input**: User description: "Build a shared evaluation harness that every case study in this casebook reuses to measure its POC and publish a results table."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Evaluate one configuration and get a results table (Priority: P1)

The author has a POC with a retrieval function and a question set. They point the harness at the question set and the POC's retrieval function, and receive a Markdown results table with the standard metrics, plus a machine-readable file with the outcome of every question.

**Why this priority**: This is the core value. Without it, no case study can back its numbers with evaluation output.

**Independent Test**: Run the harness on a 3-question sample set with a stand-in retrieval function and confirm it produces a Markdown table and a per-question results file.

**Acceptance Scenarios**:

1. **Given** a valid 3-question sample set and a retrieval function, **When** the author runs an evaluation, **Then** a Markdown table with hit rate at k, section hit rate at k, mean reciprocal rank, cross-entitlement retrievals, error count, and latency p50/p95 is produced.
2. **Given** the same run, **When** it finishes, **Then** a machine-readable results file lists, for every question, its id, the ranked results returned, and the outcome of each metric.
3. **Given** the same inputs run twice, **When** results are compared, **Then** every value is identical except latency.

---

### User Story 2 - Catch cross-entitlement retrievals (Priority: P1)

The author needs proof that a POC never returns documents the asking user is not entitled to see. Each question lists the documents that user must not see, and the harness counts every returned result that matches.

**Why this priority**: Security is a core principle of the casebook. The cross-entitlement count must be trustworthy, otherwise the security claim in a case study is unsupported.

**Independent Test**: Use a question whose expected document is also on the user's not-entitled list, return it from the retrieval function, and confirm it is counted as a cross-entitlement retrieval.

**Acceptance Scenarios**:

1. **Given** a question where the retrieval returns a not-entitled document, **When** metrics are computed, **Then** the cross-entitlement count increases by one for each such result.
2. **Given** a not-entitled document that is also the expected document, **When** it is returned, **Then** it is still counted as a cross-entitlement retrieval.
3. **Given** a run with no not-entitled documents returned, **When** the table is produced, **Then** the cross-entitlement count shows 0.
4. **Given** a returned result whose document id is missing or empty, **When** metrics are computed, **Then** that result is counted as a cross-entitlement retrieval (entitlement cannot be verified), and the question is recorded as an error and counted as a miss for hit rate, section hit rate, and mean reciprocal rank.

---

### User Story 3 - Compare configurations side by side (Priority: P2)

The author wants to compare several configurations of the same POC (for example semantic only, hybrid, and hybrid with reranking) in one table, so a design doc or article can show the trade-offs.

**Why this priority**: Comparison drives the architecture decisions, but a single-configuration run already delivers value.

**Independent Test**: Supply three configurations with different retrieval behavior and confirm the output table has one row per configuration, computed on the same question set.

**Acceptance Scenarios**:

1. **Given** three configurations and one question set, **When** the evaluation runs, **Then** the table shows one row per configuration with identical metric columns.
2. **Given** the per-question results file, **When** the author inspects it, **Then** each outcome is labeled with its configuration.

---

### User Story 4 - Measure answers: refusals and citations (Priority: P2)

When a POC also generates answers, the author supplies an answer function. The harness measures whether the system refused when it should have, whether it wrongly refused a question it should have answered, and whether every cited chunk was actually retrieved.

**Why this priority**: These metrics matter for question-answering POCs but are optional for retrieval-only POCs.

**Independent Test**: Supply an answer function for the sample set, including one question that should be refused, and confirm correct-refusal rate and citation validity appear in the table.

**Acceptance Scenarios**:

1. **Given** questions marked "should refuse" and an answer function, **When** metrics are computed, **Then** correct-refusal rate is the share of should-refuse questions that were refused.
2. **Given** questions not marked "should refuse" and an answer function, **When** metrics are computed, **Then** false-refusal rate is the share of those questions that were refused.
3. **Given** an answer that cites a chunk not among the retrieved results, **When** metrics are computed, **Then** that answer is counted as having invalid citations.
4. **Given** no answer function is supplied, **When** the table is produced, **Then** answer-based metrics are shown as not applicable and retrieval metrics are still reported.

---

### User Story 5 - Score section-level retrieval and surface failures (Priority: P2)

The author wants to know not only whether the right document was retrieved but whether the right section of it was, and wants failures of the POC's own functions to be visible rather than silently skipped.

**Why this priority**: Section-level scoring shows whether chunking and ranking land on the right policy text. Visible errors keep the published numbers honest.

**Independent Test**: Run a set where one question has an expected section, one has none, and one triggers a failure in the retrieval function; confirm the section hit rate, the miss, and the error count in the table.

**Acceptance Scenarios**:

1. **Given** a question with an expected section, **When** results contain the expected document but a different section in the top k, **Then** it counts as a document hit and a section miss.
2. **Given** a question with an expected section, **When** results contain the expected document and section in the top k, **Then** it counts as both a document hit and a section hit.
3. **Given** a question without an expected section, **When** metrics are computed, **Then** it is excluded from section hit rate and still counts toward document hit rate.
4. **Given** a question with an expected section and results that carry no section, **When** metrics are computed, **Then** it counts as a section miss; and **Given** that no result in a configuration carries a section, **Then** that configuration's section hit rate is shown as "n/a".
5. **Given** a question whose retrieval or answer function fails, **When** metrics are computed, **Then** it is counted as a miss for hit rate, section hit rate, and mean reciprocal rank, and the table shows the error count for that configuration.

---

### User Story 6 - Reproduce results from a fresh clone (Priority: P3)

A reader clones the repository and reproduces a case study's published results table by following the README.

**Why this priority**: Supports reproducibility, but depends on the stories above.

**Independent Test**: On a clean checkout, run the documented command for the sample set and compare the table with the committed one.

**Acceptance Scenarios**:

1. **Given** a fresh clone, **When** the reader runs the documented evaluation steps, **Then** the table matches the published one except for latency values.

---

### Edge Cases

- A retrieval returns an empty result list: the question counts as a miss (no hit, reciprocal rank 0) and the run continues.
- A metric category has zero questions (for example, no should-refuse questions): that metric is reported as "n/a", never as a division error or a misleading 0%, and a notes line below the table explains each "n/a" (for example "False refusal: n/a, no should-answer questions").
- The question file is missing, unreadable, or malformed (missing field, wrong type, duplicate question id, empty file): the harness stops before evaluating and reports which file, which question, and which field is wrong.
- The retrieval or answer function raises an error for one question: the failure is recorded for that question with its message, the question counts as a miss for hit rate, section hit rate, and mean reciprocal rank, the run continues, and the table reports the error count.
- The expected document is not returned in the top k: it counts as a miss at k but may still contribute to reciprocal rank if it appears lower in the ranking.
- The expected document appears in the top k but only under a different section: document hit, section miss.
- A question has no expected section: it is excluded from section hit rate only.
- A question has an expected section but the returned results carry no section: a section miss (a result without a section never matches), and the question stays in the section hit rate denominator.
- A should-refuse question has no expected document: hit rate, section hit rate, and reciprocal rank exclude it.
- There are no should-answer questions (or no should-refuse questions): false-refusal rate (or correct-refusal rate) is reported as "n/a".
- A returned result has a missing, empty, or non-text document id: fail closed. It counts as a cross-entitlement retrieval because its entitlement cannot be verified, and the question is recorded as an error, which scores as a miss for hit rate, section hit rate, and mean reciprocal rank. All other results for that question are still checked for entitlement.
- A cited chunk id appears in a different question's results but not this question's: it is invalid.
- Fewer results are returned than k: k is applied to what was returned, with no padding.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The harness MUST load a question set from a file, where each question has an id, question text, a user profile (country and grade band), the expected source document and section, a should-refuse flag, and the list of documents the user is not entitled to see.
- **FR-002**: The harness MUST validate the question set before running and report malformed files with the file, the question, and the field at fault, without crashing.
- **FR-003**: The harness MUST run each question through a retrieval function supplied by the POC, which receives the question and user profile and returns a ranked list of results, each with a document id, chunk id, score, and, where the POC can supply it, the section the chunk belongs to.
- **FR-004**: The harness MUST optionally run an answer function supplied by the POC, which returns answer text, cited chunk ids, and a refused flag.
- **FR-005**: The harness MUST compute hit rate at k, where a hit means the expected document appears in the top k results. The value of k MUST be configurable, with a default of 5.
- **FR-005a**: The harness MUST also compute section hit rate at k for questions that have an expected section, where a hit means a result in the top k matches both the expected document and the expected section. Questions without an expected section MUST be excluded from this metric. Document-level hit rate remains the primary metric and MUST be listed first in the table.
- **FR-006**: The harness MUST compute mean reciprocal rank based on the position of the first result matching the expected document, counting 0 when absent.
- **FR-007**: The harness MUST count cross-entitlement retrievals as the number of returned results whose document is on the question's not-entitled list. This MUST apply regardless of whether that document is also the expected document, and regardless of rank. A returned result with a missing, empty, or non-text document id MUST also be counted as a cross-entitlement retrieval (fail closed, since entitlement cannot be verified), and its question MUST be recorded as an error (see FR-014a).
- **FR-008**: The harness MUST compute latency p50 and p95 per configuration using the nearest-rank method, measured around each retrieval call.
- **FR-009**: The harness MUST compute correct-refusal rate as the share of should-refuse questions that the answer function refused, and false-refusal rate as the share of should-answer questions that it refused, when an answer function is supplied.
- **FR-010**: The harness MUST compute citation validity as the share of answers in which every cited chunk id was among the chunks retrieved for that question, when an answer function is supplied.
- **FR-011**: The harness MUST evaluate several configurations of the same POC against the same question set and present them side by side.
- **FR-012**: The harness MUST output a Markdown results table, ready to paste into a README or article, with one row per configuration.
- **FR-013**: The harness MUST output a machine-readable results file listing per-question outcomes (returned results, hit, reciprocal rank, cross-entitlement count, latency, refusal and citation outcomes, and any error), labeled by configuration.
- **FR-014**: The harness MUST handle empty result lists, zero-question categories, and per-question function errors with clear messages, and MUST NOT crash.
- **FR-014a**: Any question recorded as an error, for any reason (a function failure or an unverifiable result), MUST be counted as a miss for hit rate, section hit rate, and mean reciprocal rank, and as failed for the answer-based metrics (see Assumptions). It MUST stay in all metric denominators and MUST be counted in a per-configuration error count shown in the results table. Error handling MUST NOT reduce the cross-entitlement total: results with an unverifiable document id still count toward it.
- **FR-015**: The harness MUST produce identical metric values and per-question outcomes for identical inputs, excluding latency.
- **FR-016**: The harness MUST operate entirely locally, with no calls to any cloud service, and MUST be reusable by every case study without modification.
- **FR-017**: The repository MUST include a synthetic 3-question sample set and a stand-in retrieval function that demonstrate an end-to-end run.

### Key Entities *(include if feature involves data)*

- **Question**: One evaluation item. Attributes: id, question text, user profile, expected document and section, should-refuse flag, not-entitled document list.
- **User Profile**: The asking user's country and grade band.
- **Retrieval Result**: One ranked item returned by a retrieval function: document id, chunk id, score, and optionally a section.
- **Answer**: Optional output of an answer function: answer text, cited chunk ids, refused flag.
- **Configuration**: A named variant of a POC (for example "hybrid + reranker") whose retrieval, and optionally answer, behavior is evaluated.
- **Question Outcome**: The per-question, per-configuration record of results, metric values, latency, and any error.
- **Results Table**: The Markdown summary, one row per configuration.
- **Results File**: The machine-readable record of all question outcomes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The author can go from a question set and a retrieval function to a finished results table in a single command.
- **SC-002**: The 3-question sample set runs end to end and produces a results table and a results file.
- **SC-003**: 100% of results on a not-entitled list, and 100% of results with a missing or empty document id, are counted as cross-entitlement retrievals in the test suite, including the case where the document is also the expected one.
- **SC-004**: Two runs on identical inputs produce identical results files, apart from latency fields.
- **SC-005**: Every malformed-input case in the edge-case list produces a human-readable message naming the problem, with zero unhandled crashes.
- **SC-006**: A reader can reproduce a published results table from a fresh clone in under 10 minutes, per the casebook's reproducibility principle.
- **SC-007**: Three or more configurations can be compared in one table without changing the harness.
- **SC-008**: In the test suite, a document-hit/section-miss case, a case with no expected section, and a failing-function case each produce the section hit rate and error count defined above.
- **SC-009**: In the test suite, false-refusal rate and correct-refusal rate are each computed from the correct subset of questions and report "n/a" when that subset is empty.

## Assumptions

- Each case study (starting with the first, a permission-aware RAG POC) supplies its own question set and retrieval function; the harness itself contains no POC-specific logic.
- A document is the unit for hit rate, reciprocal rank, and entitlement checks. Section hit rate is reported alongside as a secondary metric.
- A result without a section never matches an expected section, so a question with an expected section whose results carry no section is a section miss. Section hit rate is "n/a" for a configuration only when no result in that configuration carries a section (or no question has an expected section).
- When some configurations in a run have an answer function and others do not, the answer-based columns appear in the table, and the configurations without an answer function show "n/a" in them.
- Latency percentiles use the nearest-rank method: the value at sorted position `ceil(p/100 × n)`. For small question sets p95 therefore equals the maximum.
- Section matching is exact on the section identifier given in the question set.
- Reciprocal rank is based on the first result from the expected document.
- The default k is 5, and the author can change it per run.
- Latency is wall-clock time of each retrieval call, so it is the only value that varies between runs.
- Question sets are stored in a plain-text structured file format chosen at planning time, and all content is synthetic, per the casebook's synthetic-data principle.
- The harness lives in the shared code area of the casebook (`shared/`) and follows the casebook's Python standards.
- Correct-refusal rate uses should-refuse questions as its denominator, and false-refusal rate uses all other questions.
- Any question recorded as an error, for any reason (the retrieval or answer function raised, or a returned result had an unverifiable document id), counts as: no document hit, no section hit, reciprocal rank 0, not a correct refusal, not a refusal (so it adds no false refusal, but is visible in the error count), and invalid citations. It stays in every denominator it would otherwise belong to. Its latency is excluded from p50/p95. The error count is the signal that the numbers include failures.
- Error handling never lowers the cross-entitlement total. Every result a function did return is still checked, and each result with a missing, empty, or non-text document id is counted as a cross-entitlement retrieval, even though its question scores as a miss. A function that raised an error returned nothing, so it adds 0.
- When a returned result has an unverifiable document id, the answer function is not called for that question, because its retrieved results cannot be trusted.
- LLM-as-judge grading (planned for Post 4), cloud service calls, and any user interface are out of scope.
