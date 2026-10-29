# ADR-006: The gateway never rewrites prompts and never silently falls back

- **Status:** Proposed
- **Date:** 2026-11-09
- **Case:** 04 · An LLM gateway that cut the bill (Google Cloud)
- **Related:** ADR-001, ADR-003

## Context

The gateway sits in front of every AI feature. Features such as prompt compression, automatic fallback to another model and "smart" rewriting were suggested. Each would change what the model sees without the owning team knowing.

## Decision

1. The gateway may **reject** a request (too large, wrong prompt order, over budget, unknown use case). It never **edits** one.
2. No automatic model fallback. A fallback is allowed only if listed in the use case's policy and evaluated for that use case.
3. Metering is asynchronous and never blocks a request.
4. Stateless, regional, several instances with a minimum instance count; timeouts per use case.
5. Gateway code changes follow the same review and test bar as payment code.

## Consequences

- Teams can trust that what they send is what the model sees.
- A model outage surfaces as an error, not a silent quality change.
- Some savings (prompt compression) are left for teams to do in their own prompts, where they can evaluate them.

## Verification

- Contract test: request bytes sent to the model equal the bytes received from the caller.
- p95 gateway overhead under 30 ms in load tests (planning target).
