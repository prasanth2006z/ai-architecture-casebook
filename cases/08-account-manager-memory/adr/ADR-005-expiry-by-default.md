# ADR-005: Expiry by default; reconfirm notes older than 90 days

- **Status:** Proposed
- **Date:** 2026-10-26
- **Case:** 08 · Memory for an account-manager assistant (AWS)
- **Related:** ADR-001

## Context

Notes go stale silently. A clean-up job that someone must remember to run is the same failure as a hand-built context (Case 03).

## Decision

1. Session events: 30 days. Preferences: 1 year. Account notes: 180 days unless reconfirmed. Meeting summaries: 2 years.
2. Configure long-term record expiry per strategy in AgentCore Memory (TTL per strategy), so expiry is configuration.
3. When a note older than 90 days is used, the briefing marks it "still true?"; yes resets the clock, no deletes it.

## Consequences

- Some valid notes expire; the reconfirmation prompt keeps the useful ones alive.
- TTL changes need the corresponding IAM permission and are reviewed like other config.

## Verification

- Expiry test: note older than 90 days flagged; note past TTL not retrievable.
- Monthly: share of notes confirmed when asked.
