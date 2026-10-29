# ADR-005: Choose the architecture with a task set, and re-run it when models or frameworks change

- **Status:** Proposed
- **Date:** 2026-12-14
- **Case:** 09 · One agent or five? A research assistant (Google Cloud)
- **Related:** Case 05 (evaluation as a release gate)

## Context

The five-agent design was chosen from a diagram and a demo. Measurement on real questions reversed the decision within a day.

## Decision

1. Maintain a task set: 40 past questions with analyst-written reference briefs, including a broad-question subset.
2. Metrics: key-fact recall (judge model, pinned, calibrated on 10 analyst-scored briefs), citation errors (code), cost and time per brief.
3. Any architecture change (new agent, new model, new framework feature) runs the task set before adoption.

## Consequences

- Architecture debates become measurements.
- The task set needs an owner and periodic refresh.

## Verification

- Comparison table updated with each change; decision recorded with numbers.
