# ADR-001: All model calls go through one gateway; only the gateway can call models

- **Status:** Proposed
- **Date:** 2026-10-26
- **Case:** 04 · An LLM gateway that cut the bill (Google Cloud)
- **Related:** ADR-002 (metering), ADR-005 (budgets)

## Context

Nine apps call Gemini models directly using their own service accounts, two API keys and one shared key. Spend grew from ~$11k to ~$48k a month. Every call lands in the same project, so the bill shows models and tokens, not apps, features or teams. There is no shared place to enforce budgets, retries, caching or model choice.

## Decision

1. Deploy one **LLM gateway** on Cloud Run with internal ingress and IAM authentication.
2. Remove model-calling permission from every principal except the gateway's service account. Revoke the API keys.
3. Apps call the gateway with an ID token from their own service account. The gateway identifies the caller from the token, never from the request body.
4. Every request names a **use case** (`claims-summary`, `nightly-enrichment`, …). A use case is the unit of ownership, budget, routing and caching. The gateway checks the caller is allowed to use it.
5. Alert on any model call made by a principal other than the gateway.

## Options considered

| Option | Why not chosen |
|---|---|
| Keep direct calls, add labels | Labels are voluntary; no enforcement point for budgets, caching or tiers |
| Apigee as the AI gateway | Good fit (LLM token quota and prompt-limit policies, semantic-cache support) **if Apigee is already run**; we don't, and adopting it for five functions is a large step |
| Open-source LLM proxy on Cloud Run/GKE | Capable, but a third-party component on the hot path that we must patch, secure and understand |
| **Thin own gateway on Cloud Run** | **Chosen.** Does exactly five jobs; small enough to test thoroughly |

## Consequences

- One place to meter, limit, cache and route.
- The gateway is on the critical path of every AI feature; it must be stateless, multi-instance and boring (ADR-006).
- Teams lose direct model access; onboarding a new use case means adding a policy entry.

## Verification

- IAM audit: only the gateway service account holds model-calling permission in the project.
- 100% of model calls in Cloud Audit Logs come from the gateway principal for 30 days.
