# ADR-003: Retrieval is scoped to one account, after a CRM access check in code

- **Status:** Proposed
- **Date:** 2026-10-26
- **Case:** 08 · Memory for an account-manager assistant (AWS)
- **Related:** Case 01 ADR-002 (access decided by data, not the model)

## Context

Acme's discount appeared in a Globex briefing because retrieval covered every account in the AM's history.

## Decision

1. Every briefing names one account. Retrieval reads only that account's namespaces plus the AM's own preferences.
2. Before any retrieval or tool call for an account, code checks account-team membership in the CRM. If absent, nothing is retrieved.
3. There is no cross-account memory search. Cross-account questions are answered from CRM reports.
4. One retrieval function owns this logic; tools do not call memory directly.

## Consequences

- Some useful questions ("which accounts mentioned X?") move to reporting.
- Access follows CRM team changes immediately.

## Verification

- Cross-account seed test: zero leaks in text or retrieved records (hard gate).
- Static check: no code path calls memory retrieval without the access check.
