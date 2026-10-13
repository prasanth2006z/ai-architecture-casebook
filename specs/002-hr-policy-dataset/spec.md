# Feature Specification: Synthetic HR Policy Dataset

**Feature Branch**: `002-hr-policy-dataset`

**Created**: 2026-10-12

**Status**: Draft

**Input**: User description: "Build the synthetic dataset for case study 01 (permission-aware RAG for HR policies), used by all five Post 1 POCs. It must reproduce the failure conditions of the mocked company Globex: wrong-country answers, a leaked restricted executive policy, and quoted superseded versions. All content is synthetic (constitution Principle III)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Policy corpus with deliberate failure conditions (Priority: P1)

A POC author needs a corpus of about 50 synthetic HR policy documents (UK and India; grade bands G1-6 and G7+; topics: leave, parental leave, travel, expenses, remote work, benefits) so that each known failure mode of the Globex chatbot can be reproduced and then shown to be fixed.

**Why this priority**: Without the corpus, no POC can run and no question can be answered. It is the foundation for everything else.

**Independent Test**: Inspect the corpus and its metadata alone: count documents and check that each failure condition (near-identical country versions, restricted documents, superseded versions, split rule/condition sections, injection probe) is present and findable.

**Acceptance Scenarios**:

1. **Given** the finished corpus, **When** a reviewer compares a UK and an India version of the same policy, **Then** the wording is near-identical and differs mainly in numbers, country names and policy codes.
2. **Given** the corpus, **When** a reviewer looks at restricted policies (e.g. executive relocation, executive compensation), **Then** their metadata allows only grade band G7+.
3. **Given** the corpus, **When** a reviewer looks for policies with older versions, **Then** a few policies have a superseded version stored alongside the current one, each marked with its status.
4. **Given** any document, **When** a reviewer reads it, **Then** it has numbered sections, and in some documents an entitlement (e.g. section 3.1) is separated from its eligibility condition (e.g. section 3.2).
5. **Given** the corpus, **When** a reviewer searches for instruction-like text, **Then** exactly one document contains an embedded instruction (a prompt-injection probe), written as clearly synthetic test content.

---

### User Story 2 - Complete, consistent document metadata (Priority: P1)

A POC author needs, for every document, its id, title, country list, allowed grade bands, version, effective date and status (current or superseded), so that access filters and version filters can be built and checked.

**Why this priority**: Entitlement and version correctness are judged against this metadata; it is the ground truth for the evaluation.

**Independent Test**: Check that every document has all seven metadata fields with valid values, and that every document has exactly one metadata entry and vice versa.

**Acceptance Scenarios**:

1. **Given** the dataset, **When** metadata is checked against the corpus, **Then** every document has one complete entry and no entry lacks a document.
2. **Given** a policy with a superseded version, **When** metadata is read, **Then** exactly one version is current, and the superseded one has an earlier version number and effective date.

---

### User Story 3 - 60-question evaluation set (Priority: P1)

A POC author needs 60 evaluation questions in the shared harness question-file format: 30 single-country, 15 where the right answer differs by country, 10 out-of-scope (to be refused) and 5 where the asker is not entitled to the most relevant document. Each names the asker's country and grade band, expected document and section, whether to refuse, and the documents the asker may not see.

**Why this priority**: The questions are what every POC is scored on; the Post 1 results tables depend on them.

**Independent Test**: Run the harness's question-file validation on the set and a consistency check against the metadata; both must pass without errors.

**Acceptance Scenarios**:

1. **Given** the question set, **When** it is validated by the shared harness, **Then** it passes with no errors.
2. **Given** the question set, **When** questions are counted by category, **Then** there are 30, 15, 10 and 5, totalling 60.
3. **Given** a not-entitled probe with an entitled fallback (3 of the 5 probes), **When** its expected outcome is read, **Then** it is not a refusal, its expected document is the entitled, current fallback (e.g. the standard relocation policy for a G1-6 asker), and its not-entitled list contains the restricted document most relevant to the question.
4. **Given** a not-entitled probe with no entitled coverage (2 of the 5 probes), **When** its expected outcome is read, **Then** it is a refusal with no expected document, and its not-entitled list contains the restricted document that would otherwise answer it.
5. **Given** a country-differing question, **When** asked by a UK user and by an India user, **Then** the expected documents differ and each is the asker's own country version.
6. **Given** any question, **When** its not-entitled list is compared with the metadata, **Then** it contains every document whose country list excludes the asker's country (all documents for the other country) plus every document whose allowed grade bands exclude the asker's grade, and no global document that includes the asker's country.

---

### User Story 4 - Verifiable integrity and reproducibility (Priority: P2)

A reviewer needs automated checks proving the dataset meets its own rules and that regenerating it gives identical files.

**Why this priority**: Constitution Principles III, IV and IX require synthetic labeling, automated acceptance checks and reproducibility; the checks are only useful once the data exists.

**Independent Test**: Build the dataset twice from a clean state and compare the files.

**Acceptance Scenarios**:

1. **Given** the same inputs, **When** the dataset is built twice, **Then** all files are identical.
2. **Given** any document or question, **When** it is checked, **Then** it is labeled synthetic and contains no real company, person or personal data.

---

### Edge Cases

- A G1-6 user's most relevant document is G7+-only: the expected document must be an entitled one, or the question must be a refusal.
- The best match exists as both a current and a superseded version: the expected document is always the current one.
- A near-identical UK/India pair: each question names a country so exactly one version is correct.
- Out-of-scope questions have no expected document and are marked as refusals.
- The injection-probe document must remain a legitimate, answerable policy for ordinary questions.
- Country and grade values in questions must match the spellings used in the metadata.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The dataset MUST contain about 50 synthetic HR policy documents for UK and India covering leave, parental leave, travel, expenses, remote work and benefits.
- **FR-002**: Country versions of the same policy MUST be near-identical in wording, differing mainly in numbers, country names and policy codes.
- **FR-003**: Every document MUST have numbered sections, and some documents MUST place an entitlement and its eligibility condition in separate sections (e.g. 3.1 and 3.2).
- **FR-004**: A few restricted policies (including executive relocation and executive compensation) MUST be visible only to grade band G7+.
- **FR-005**: A few policies MUST have a superseded older version stored alongside the current one.
- **FR-006**: Exactly one document MUST contain embedded instruction-like text acting as a prompt-injection probe, identified in the dataset documentation.
- **FR-007**: Every document MUST have metadata: document id, title, country list, allowed grade bands, version, effective date and status (current or superseded).
- **FR-004a**: Country MUST be an access restriction (consistent with ADR-002 in the case study design): a user may see a document only if its country list includes the user's country and its allowed grade bands include the user's grade band. A small number of global documents (e.g. code of conduct) MUST list both countries and be visible to both.
- **FR-008**: The dataset MUST include 60 evaluation questions: 30 single-country, 15 country-differing, 10 out-of-scope (refused), 5 not-entitled probes. Of the 5 probes, 3 MUST have an entitled, current fallback document as the expected answer and 2 MUST be refusals because no entitled document covers the question.
- **FR-009**: Each question MUST state the asker's country and grade band, expected document and section, whether it should be refused, and the documents the asker may not see, in the shared harness question-file format (specs/001-eval-harness/contracts/question-file.md).
- **FR-010**: Every non-refusal question's expected document MUST be one the asker is entitled to see and MUST be a current version; the expected section MUST exist in that document.
- **FR-011**: Every not-entitled list MUST match the metadata exactly: all documents whose country list excludes the asker's country (i.e. all other-country documents) plus all documents whose allowed grade bands exclude the asker's grade band. Global documents that include the asker's country are never listed.
- **FR-012**: Every document and question MUST be labeled synthetic and MUST contain no real company, person or personal data.
- **FR-013**: The dataset MUST be reproducible: the same inputs always yield identical files.
- **FR-014**: Automated checks MUST verify FR-001 to FR-013, and the question set MUST pass the harness's question-file validation without errors.

### Key Entities

- **Policy document**: A synthetic HR policy with numbered sections, belonging to one topic and one or more countries.
- **Document metadata**: The seven descriptive fields of a policy document; the ground truth for entitlement and version.
- **Evaluation question**: A question with asker profile, expected document and section, refusal flag and not-entitled list.
- **Asker profile**: Country (UK or India) and grade band (G1-6 or G7+); determines entitlement.
- **Question category**: Single-country, country-differing, out-of-scope, or not-entitled probe.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The corpus holds 45-55 documents, covering all six topics in both countries.
- **SC-002**: 100% of the 60 questions pass the harness's question-file validation with zero errors.
- **SC-003**: 100% of non-refusal questions point to a document the asker is entitled to and that is current (zero violations).
- **SC-004**: 100% of not-entitled lists agree with the metadata (zero mismatches).
- **SC-004a**: Of the 5 not-entitled probes, exactly 3 expect an entitled current fallback document and exactly 2 are refusals; a small number of global documents exist and appear in no asker's not-entitled list.
- **SC-005**: 100% of documents and questions carry the synthetic label; zero real company, person or personal data found in review.
- **SC-006**: Building the dataset twice gives identical files in 100% of runs.
- **SC-007**: Each of the five failure conditions (wrong country, restricted leak, superseded version, split rule/condition, injection) is covered by at least 3 questions or documents a reviewer can point to.

## Assumptions

- Country values are UK and India; grade bands are G1-6 and G7+ (restricted documents allow G7+ only; all others allow both).
- Country is an access restriction, not just a relevance hint: entitlement requires both country and grade match, so other-country documents appear in every asker's not-entitled list. A small number of global documents (e.g. code of conduct) list both countries.
- Evaluation use: POC 2 measures retrieval without the security filter (so it can show cross-country and restricted leakage), and POC 3 measures retrieval with the security filter applied. The same questions and not-entitled lists serve both.
- Because country is a restriction, a "wrong-country answer" counts as an entitlement violation as well as a relevance error.
- Globex is a fictional placeholder company name, used only as a synthetic label.
- The question file is JSONL as defined by the shared harness contract and lives under the case study's `evals/` folder.
- The existing eval harness validation is reused, not reimplemented.
- Out of scope: loading data into any cloud service, embeddings, and any retrieval code.
- Dataset content may be drafted with AI help, but the author reviews it; entitlement ground truth is derived from the metadata, not written by hand twice.
