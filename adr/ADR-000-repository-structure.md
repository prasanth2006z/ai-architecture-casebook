# ADR-000: Split the casebook into focused repositories

Status: Accepted · Date: 2026-10-15

## Context
Everything lived in one repository: design docs and ADRs, the shared evaluation harness, the case 01 POC, Spec Kit tooling and a paused dataset branch. Readers from the Medium series come for the design thinking and have to dig through tooling to find it. The harness is shared by every case and needs its own versions, while each case POC has its own lifecycle and is currently paused.

## Decision
- `ai-architecture-casebook` (public): design docs and ADRs only, one folder per case under `cases/`, plus casebook-wide decisions under `adr/`.
- `ai-eval-harness`: the shared evaluation harness with its own specs, Spec Kit setup and tagged releases. Cases pin a released version.
- One POC repository per case (for example `case-01-permission-aware-rag`), created only when that POC is actively built. Case-specific datasets live in the case repository, not in the harness.

History is preserved with `git filter-repo`. The pre-split state is kept as tags (`archive/pre-split-main`, `archive/002-hr-policy-dataset`).

## Alternatives rejected
- Keep the monorepo: one place to change things, but the public face mixes thinking with tooling, and the harness cannot be versioned independently.
- One repository per part immediately (docs, harness, datasets, each POC): clean on paper, but creates empty repositories and cross-repo overhead for work that is paused.
- Git submodules linking the parts: adds friction for every clone and update, for little benefit at this size.

## Consequences
A change that touches both the harness and a case needs two commits and a version bump. Each repository with code needs its own README, CI and Spec Kit constitution. The docs repository needs no build at all.

## Revisit when
Cross-repository changes become frequent enough that coordinating versions costs more than it saves.
