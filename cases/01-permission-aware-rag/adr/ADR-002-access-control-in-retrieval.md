# ADR-002: Enforce access control with an explicit metadata filter built from the token

Status: Accepted · Date: 2026-10-20

## Context
A junior employee received restricted executive policy text. Entitlements depend on country and grade, which come from the corporate identity provider through Cognito (requirement R1). A user may only see documents whose country list includes their country and whose grade bands include their grade.

## Decision
Every document carries `allowed_countries` and `allowed_grades` lists in its metadata. The Lambda builds a mandatory `andAll` filter of `listContains` conditions from the user's verified token claims and passes it in every `Retrieve` call. The model only ever receives chunks the user is entitled to see.

## Alternatives rejected
- Bedrock implicit metadata filtering: a model-generated filter is controlled by the user's words, so it must never carry security. It may be added later for relevance only, alongside the explicit filter.
- Telling the model in the prompt which documents the user may see: the model has already received the restricted text, and prompt instructions can be bypassed through prompt injection.
- Filtering results after retrieval in application code: restricted chunks take slots in the candidate list, hurting quality, and one bug leaks data.
- A separate knowledge base per country and grade: dozens of indexes to keep in sync, with duplicated documents and cost.

## Consequences
Country and grade claims must be correct in the identity provider; a stale grade can briefly hide or show a document. R1 is tested with dedicated cross-entitlement probe questions, and the shared evaluation harness counts any unverifiable result as a leak (fail closed). The `listContains` operator is best supported on OpenSearch Serverless, which ties this ADR to ADR-001.

## Revisit when
Entitlements become per person rather than per attribute, which points toward a dedicated authorization service or a connector-level ACL product.
