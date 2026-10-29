# ADR-004: Run the fleet as resumable jobs with per-repository state

- **Status:** Proposed
- **Date:** 2026-10-26
- **Case:** 07 · A loop agent that upgrades 300 repositories (Google Cloud)

## Context

The pilot kept no state. Crashes restarted repositories from scratch, and nobody could say how far the fleet had got.

## Decision

1. One Firestore record per repository (status, wave, script commit, iterations, last error, test counts, PR URL).
2. A Cloud Run job runs one task per repository, max 20 concurrent (set by CI capacity and model quota).
3. Every step is idempotent and reads state first; a rerun continues from the last finished step.
4. A dashboard over the state shows progress by team and wave.

## Options considered

| Option | Why not chosen |
|---|---|
| One long script on a VM | No parallelism control; no resume |
| Cloud Workflows per repo | Workable; more moving parts than needed for a fixed sequence |

## Consequences

- The fleet can be paused (stop scheduling tasks) and resumed safely.
- Concurrency is a single setting tuned to CI and quota.

## Verification

- Kill a task mid-agent-loop; rerun resumes at the recorded iteration.
