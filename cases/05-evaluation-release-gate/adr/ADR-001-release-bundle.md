# ADR-001: Version everything that changes an answer as one release bundle

- **Status:** Proposed
- **Date:** 2026-11-16
- **Case:** 05 · Evaluation as a release gate (AWS)
- **Related:** Case 01, Case 04 ADR-003 (tier changes are releases)

## Context

In six weeks the HR assistant changed model version, chunking, policy data and prompt, through different routes (console edits, data loads, code). No change could be named or compared, and after the Friday incident nobody could tell which answers were produced by which configuration.

## Decision

1. Define a **release bundle**: model ID (pinned), inference settings, prompt file version, retrieval settings (knowledge base, data snapshot, chunking version, top-k), guardrail version.
2. The bundle is one manifest file in git; its ID is immutable.
3. Production runs exactly one bundle (plus one candidate during a canary). The bundle ID is written to every log line and trace.
4. Nothing changes outside a bundle: no console prompt edits in production; a data load creates a snapshot that only goes live through a new bundle.

## Options considered

| Option | Why not chosen |
|---|---|
| Version only the prompt | Model, data and retrieval changes also change answers |
| Tag deployments only | Data loads and console edits bypass deployments |

## Consequences

- Every change, including a data refresh, goes through the gate (ADR-004).
- Data refreshes need a snapshot mechanism in the knowledge base pipeline.
- Incident review can reproduce any answer's configuration.

## Verification

- 100% of answer logs carry a known bundle ID.
- Attempted console edit to the production prompt is denied by IAM.
