# AI Architecture Casebook Constitution

A public repository of real-world AI system design case studies. Each case study ships a design doc, Architecture Decision Records (ADRs), and proof-of-concept (POC) code on AWS or GCP.

## Core Principles

### I. Architecture Decisions First
Every POC implements a decision recorded in an ADR. Code links to the ADR it proves (module docstring or README reference). A POC with no ADR is not accepted; if the code reveals the decision was wrong, update the ADR first.

### II. Security by Construction
- Access-control filters are built only from verified identity claims (e.g., validated token claims), never from user input or model output.
- No secrets in code or config files. Credentials come from the environment or a secrets manager.
- Security-relevant behavior is covered by tests that attempt to violate it (e.g., a prompt-injected query must not widen a filter).

### III. Synthetic Data Only
No real company, customer, or personal data, ever. All datasets, names, documents, and scenarios are synthetic and labeled as such. Case studies describing real-world patterns must be generalized and anonymized.

### IV. Evaluation Is Mandatory
- Every POC ships an evaluation script that produces a Markdown results table.
- Acceptance criteria from the spec become automated tests.
- Claims in a design doc or ADR about quality, latency, or cost must be backed by the evaluation output or explicitly marked as unverified.

### V. Cost Control
- Every cloud resource is created with Terraform.
- Every POC has a one-command teardown (e.g., `terraform destroy` in the POC's `infra/` folder).
- Nothing is left running; READMEs state expected cost and teardown steps up front.

### VI. Simplicity
Write the smallest code that proves the decision. No production plumbing (UIs, CI pipelines, full networking) unless the spec requires it. Complexity must be justified in the ADR or spec.

### VII. Python Standards
Python 3.12 managed with uv; pytest for tests; type hints on all functions; small, single-purpose functions; ruff for linting and formatting. Dependencies are declared in `pyproject.toml` and locked.

### VIII. Human Review
The author reviews every change, including AI-generated ones.
- Security-critical code (access-control filters, authentication, entitlement checks) is written by the author, not accepted from generated output.
- Evaluation-core code (metric calculations) may be drafted by Claude, but the author reviews it line by line and rewrites any part they cannot explain.

### IX. Reproducibility
Every POC folder has a README that runs from a fresh clone in under 10 minutes: prerequisites, setup, run, evaluate, teardown. Steps are copy-pasteable and tested on a clean checkout.

## Required Layout per Case Study
Each case study lives in a numbered folder (e.g. `01-permission-aware-rag/`) containing:
- `docs/design.md`
- `docs/adr/` (numbered ADRs using `templates/adr-template.md`)
- `docs/diagrams/`
- `specs/` (Spec Kit artifacts per POC)
- `src/` (code and tests)
- `infra/` (Terraform with one-command teardown)
- `evals/` (datasets and results tables)
- `README.md` (run, evaluate, teardown, results)

Shared reusable code lives in `shared/`.

## Governance
This constitution supersedes other practices. Every spec, plan, and review must check compliance with these principles.

- **Amendments**: require a recorded rationale and a version bump. The repository author approves every amendment.
- **Versioning**: amendments follow semantic versioning.
  - MAJOR: remove or redefine a principle.
  - MINOR: add a principle or materially expand guidance.
  - PATCH: wording and clarifications.
- **Compliance review**: compliance is reviewed at the Reconcile stage of every case study. Any deviation is recorded and justified in that case study's ADRs.

- **Amendment 1.0.1 (2026-10-11, PATCH)**: Principle VIII now separates security-critical code (author-written) from evaluation-core code (Claude may draft; the author reviews line by line and rewrites what they cannot explain). Rationale: the earlier wording "written or rewritten" was ambiguous for metric calculations, and a clarification avoids two readings of the same rule.

**Version**: 1.0.1 | **Ratified**: 2026-10-11 | **Last Amended**: 2026-10-11
