# ADR-001: Use hybrid search on OpenSearch Serverless with a reranker

Status: Accepted · Date: 2026-10-09

## Context
HR policies exist in near-identical versions per country. The first chatbot confused them because, semantically, they are almost the same text. Retrieval must catch exact terms (country, policy code, grade) as well as paraphrased questions (requirement R3).

## Decision
Use a Bedrock Knowledge Base backed by Amazon OpenSearch Serverless, query it with search type `HYBRID` (vector plus raw-text search), then rerank with a Bedrock reranker model and keep the top 5.

## Alternatives rejected
- Vector only: misses exact-term distinctions; this caused the wrong-country answers.
- Keyword only: fails on paraphrases such as "time off after having a baby".
- Amazon S3 Vectors as the store: much cheaper, but Bedrock Knowledge Bases support hybrid search only on RDS, OpenSearch Serverless and MongoDB stores; elsewhere the query silently falls back to semantic search.
- Aurora PostgreSQL with pgvector: supports hybrid, but the team would own database sizing and tuning.

## Consequences
OpenSearch Serverless has a minimum capacity cost even when idle, which dominates spend at low volume, so POC infrastructure must be torn down after each session. Reranking adds latency, measured in POC 2 against the 3-second target.

## Revisit when
A hit-rate test shows semantic-only matches hybrid on our data (then S3 Vectors becomes the cheaper choice), or the OpenSearch Serverless minimum cost breaks the R9 budget.
