# ADR-003: Route by use case to a model tier; tier changes need a passing evaluation

- **Status:** Proposed
- **Date:** 2026-11-09
- **Case:** 04 · An LLM gateway that cut the bill (Google Cloud)
- **Related:** Case 05 (evaluation as a release gate), ADR-006

## Context

Every app defaulted to a Pro-class model. Metering showed 62% of spend on tasks (classification, short extraction, summarisation) where a Flash-class model passed the same tests. A per-request "smart router" was proposed.

## Decision

1. Each use case is configured with a **tier** (`flash-lite`, `flash`, `pro`) in the policy file.
2. Tiers map to **pinned model versions** in the gateway config. Changing the map is a release and goes through the evaluation gate (Case 05).
3. To move a use case to a cheaper tier, its owner runs the use case's golden set against both tiers. If the cheaper tier is within the agreed margin, the policy changes.
4. No per-request routing by a model. The gateway never reads a request to decide which model to use.

## Options considered

| Option | Why not chosen |
|---|---|
| Cheapest model for everyone | Breaks the use cases that need a stronger model; quality loss is hidden |
| Per-request LLM router | Adds a model call to every request; quality depends on an unevaluated classifier |
| Provider-side automatic routing | Same issue: the routing decision isn't evaluated against our use cases |
| **Tier per use case, evaluation-gated** | **Chosen.** Simple, testable, reversible in config |

## Consequences

- Six of nine use cases moved down a tier in this scenario; two stayed on Pro.
- Every use case needs a golden set. That is work, and it is the bottleneck for savings.
- Model upgrades become explicit, testable events instead of silent changes.

## Verification

- No use case changes tier without a recorded evaluation run.
- Online sampling of task success per use case shows no drop after a tier change.
