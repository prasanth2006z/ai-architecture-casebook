# ADR-001: One agent by default; split only for parallel work, a clean context or a different permission

- **Status:** Proposed
- **Date:** 2026-12-14
- **Case:** 09 · One agent or five? A research assistant (Google Cloud)
- **Related:** ADR-002, ADR-005

## Context

The five-agent design mirrored a human team (planner, searcher, reader, analyst, writer). It cost ~14× a single agent, was slower, and produced citation errors through summaries of summaries. A single agent lost recall on broad, many-source questions.

## Decision

1. Default to one model call per step, not one agent per role.
2. Add an agent only for one of three measurable reasons:
   - **Parallel work** (independent steps at the same time);
   - **A clean context** (isolate inputs that would otherwise be mixed up);
   - **A different permission** (tools or data other steps must not have).
3. Here: readers are separate agents (parallel + clean context). Planning and writing are single steps. The "analyst" role is removed.

## Consequences

- Fewer hand-offs, fewer tokens, easier debugging.
- A future licensed-source reader is justified by permission, not by role.

## Verification

- Any new agent proposal names its reason and the metric it should improve on the task set (ADR-005).
