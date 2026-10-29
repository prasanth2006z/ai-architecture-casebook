# ADR-005: Canary deployment with online evaluation and automatic rollback

- **Status:** Proposed
- **Date:** 2026-11-16
- **Case:** 05 · Evaluation as a release gate (AWS)
- **Related:** ADR-003, ADR-004

## Context

The offline gate only covers questions someone thought of. Real users ask new things, and some failures show up only on real traffic.

## Decision

1. The assistant runs on Lambda; the bundle ID is part of the deployed version.
2. CodeDeploy shifts 10% of traffic to the new version first.
3. During the canary, a sampler scores a sample of live conversations with the same deterministic checks and judge. If hosted on Amazon Bedrock AgentCore, AgentCore Evaluations (online evaluation of sampled traces) may replace the sampler.
4. CloudWatch alarms on leak > 0 or online scores below the production baseline trigger automatic rollback.
5. Promote to 100% after the canary window passes.

## Consequences

- Online scoring of real conversations needs a data-handling decision (retention, who can read samples).
- Canary windows slow releases slightly.

## Verification

- Game day: deploy a bundle with a known regression; canary alarm rolls it back.
