# ADR-003: Deterministic checks first; a pinned, calibrated judge only for judgement

- **Status:** Proposed
- **Date:** 2026-11-16
- **Case:** 05 · Evaluation as a release gate (AWS)
- **Related:** Case 01 ADR-002 (security from verified data, never from model output)

## Context

Some properties have exact answers (was the expected section retrieved, was a citation given, did any document outside the entitlement appear, did the assistant refer to HR). Others need judgement (faithfulness, completeness). Using a judge model for everything adds cost, delay and randomness; using it for leaks would let a model decide whether data leaked.

## Decision

1. **Layer 1, deterministic (every run):** retrieval hit@8 on expected section; citation present and among retrieved sections; leaks = 0 from entitlement data; behaviour from a structured `answered | referred_to_hr` field; no other country's policy cited.
2. **Layer 2, judge (every run):** faithfulness, key-fact correctness, completeness, clarity. Run via Amazon Bedrock evaluation jobs (RAG evaluation with LLM-as-judge and custom metrics) or an own harness.
3. Judge rules: pinned version (a judge change is its own release); calibrated against ~100 HR-labelled answers; run 3× on production weekly to measure the noise band.
4. **Layer 3, people:** 20 answers reviewed by HR for model upgrades, new countries and new policy types.

## Consequences

- The assistant must return a structured behaviour field alongside its text.
- Judge cost scales with golden-set size × runs; tracked per run.

## Verification

- Judge agreement with HR labels above the agreed level before each quarter.
- Leak check never depends on model output (code review rule).
