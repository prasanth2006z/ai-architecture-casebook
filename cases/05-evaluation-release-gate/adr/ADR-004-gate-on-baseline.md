# ADR-004: Hard gates are absolute; soft gates compare with production

- **Status:** Proposed
- **Date:** 2026-11-16
- **Case:** 05 · Evaluation as a release gate (AWS)
- **Related:** ADR-002, ADR-003

## Context

Fixed thresholds ("faithfulness ≥ 0.85") fail in two ways: they pass a release that is worse than production but above the bar, and they fail good releases when the judge's scale drifts. Judge scores also vary between runs.

## Decision

1. **Hard gates:** leaks = 0; must-pass = 100%. Failing either = `fail`.
2. **Soft gates:** for retrieval hit@8, citation rate, faithfulness, correctness, p95 latency and cost per answer, compare the candidate with the production bundle **run the same day with the same judge**. A drop larger than the metric's noise band plus tolerance (1 point; 15% for latency/cost) = `needs_review`.
3. **Hold-out rule:** if core rises while hold-out falls beyond noise = `needs_review` (overfitting).
4. `needs_review` may ship only with a written reason in the pull request. Overrides are counted monthly.

## Options considered

| Option | Why not chosen |
|---|---|
| Absolute thresholds | Pass regressions above the bar; brittle to judge drift |
| Human sign-off only | Slow; inconsistent; skipped under pressure |

## Consequences

- Every gate run executes the golden set twice (candidate and production).
- Noise bands must be measured and kept current.

## Verification

- Replay of the Friday change: gate returns `fail` (must-pass 88%).
- Override count reviewed monthly.
