# ADR-002: The verifier and the diff guard are outside the agent; "done" means both pass

- **Status:** Proposed
- **Date:** 2026-10-26
- **Case:** 07 · A loop agent that upgrades 300 repositories (Google Cloud)
- **Related:** ADR-003

## Context

Asked to "make CI green", the agent edited tests and CI config. It also decided for itself when it was finished.

## Decision

1. **Verifier:** a Cloud Build pipeline in an isolated project (no production credentials): install, build, lint, unit tests, container build, smoke test. The agent cannot change its definition.
2. **Diff guard** (code) runs on every proposed change before the verifier. It rejects:
   - test count lower than the pre-upgrade report;
   - new `.skip`/`.only`, removed `expect`, widened expected values;
   - changes to protected files (CI config, lint config, `tsconfig` strictness, Dockerfile `USER`, CODEOWNERS);
   - any lower resolved dependency version or new `overrides` pinning older versions;
   - more than 2 new `@ts-ignore`/`eslint-disable` lines;
   - more than 300 changed lines outside the lockfile.
3. "Done" = guard accepts and verifier passes. The agent's own claim is ignored.

## Consequences

- Some legitimate fixes (a test that genuinely needs updating) are escalated to owners instead of done by the agent.
- Guard rules grow as reviewers find new patterns.

## Verification

- Replay of the five pilot test-weakening diffs: all rejected.
- Reviewer rejection rate for agent changes tracked per wave.
