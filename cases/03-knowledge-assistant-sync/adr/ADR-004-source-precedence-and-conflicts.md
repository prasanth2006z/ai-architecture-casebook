# ADR-004: Each source is authoritative for one question; show conflicts

- **Status:** Accepted
- **Date:** 2026-10-18
- **Case:** 03 · Keeping a team knowledge assistant in sync (GCP)
- **Related:** ADR-003

## Context

Specs, code and schema often disagree: a spec describes behaviour that was never built, code does something the spec does not mention, the schema has a column nobody documented. A merged answer hides this.

## Decision

Precedence by question:

| Question | Authoritative source |
|---|---|
| What exists? (tables, columns, status values) | Schema catalog |
| What happens? (current behaviour) | Code in production (`prod` tag) |
| What was intended? (business rule) | Confluence spec |

When sources disagree, the assistant **cites both and says they disagree**. It does not choose silently. It suggests the feature owner as the person to resolve it.

The nightly reconcile also produces a **drift report** for the team:

- status values in the database not mentioned in any Confluence page,
- columns without comments,
- Confluence pages that refer to tables or columns that no longer exist.

## Consequences

- Answers can be longer when sources disagree, but they are honest.
- Documentation gaps become visible as a weekly list instead of surprises.

## Verification

- Golden-set questions with known conflicts must produce an answer that cites both sources.
- Drift report generated nightly; count trended over time.
