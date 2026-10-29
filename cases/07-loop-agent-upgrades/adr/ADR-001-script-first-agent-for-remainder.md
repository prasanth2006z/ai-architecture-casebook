# ADR-001: Deterministic script first; the agent only works on remaining failures

- **Status:** Proposed
- **Date:** 2026-11-30
- **Case:** 07 · A loop agent that upgrades 300 repositories (Google Cloud)
- **Related:** ADR-002, ADR-005

## Context

Most of a Node.js major upgrade is identical across repositories: `engines`, `.nvmrc`, Docker base image, CI runtime, `@types/node`, lockfile, and known deprecations from the release notes. In the pilot, the agent did all of it, producing large, inconsistent diffs.

## Decision

1. Every repository first gets a versioned **upgrade script**: mechanical edits plus codemods, committed as one commit.
2. Run the verifier. If green, open a script-only pull request; no model involved.
3. The agent starts only on a red build after the script, with the specific failure as its task.

## Consequences

- 190 of 300 repositories (planning figure) finish with zero model calls and uniform diffs.
- The script is code that reaches every repository; it is tested on wave 1 before wider use.

## Verification

- Script-only PRs have identical file sets except lockfiles.
- Share of repos finished by script tracked per wave.
