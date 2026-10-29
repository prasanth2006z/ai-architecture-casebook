# ADR-002: A golden set in three parts, with a hidden hold-out; incidents add items

- **Status:** Proposed
- **Date:** 2026-11-16
- **Case:** 05 · Evaluation as a release gate (AWS)
- **Related:** ADR-003, ADR-004, Labs track (Lab 1)

## Context

The assistant's correct answer depends on the user (country, grade, entitlements). The most damaging failure was an answer that should have been a referral to HR. A single flat test set invites tuning prompts to pass it.

## Decision

1. Build ~250 items from real, anonymised questions. Each item has: question, user profile, expected behaviour (answer/refuse), section that must be cited, key facts, countries that must not be cited.
2. Split into:
   - **Must-pass** (~40): leaks, refusals, wrong-country cases, every past incident. 100% required.
   - **Core** (~150): stratified by country and topic. Compared with production.
   - **Hold-out** (~60): same mix as core, never visible to prompt authors.
3. Every production incident adds the failing case and variations to must-pass.
4. HR policy owners own the must-pass set; refresh the hold-out quarterly.

## Consequences

- Building and maintaining the set is ongoing work with a named owner.
- The hold-out lives in a location prompt authors can't read; the gate reads it.

## Verification

- Every incident in the last quarter has a matching must-pass item.
- Coverage report: every country and top-10 topic has at least 5 core items.
