# AI Architecture Casebook

Real-world AI problems worked through the way an architect would: requirements, options, trade-offs, decisions and how to prove the result works. Each case is a mocked but realistic problem on AWS or GCP, with a design document and Architecture Decision Records (ADRs).

The series is published on Medium: [Designing AI Systems with an API Mindset] (https://medium.com/@prasanth_pattathil/51131e78a179)

## Cases

| # | Case | Medium post | Design and ADRs |
|---|------|-------------|-----------------|
| 01 | Permission-aware RAG for HR policies | [Designing a RAG System That Knows What You're Allowed to See](https://medium.com/@prasanth_pattathil/7ac66c3f81eb) | [cases/01-permission-aware-rag](cases/01-permission-aware-rag) |

More cases are added as posts are published.

## Related repositories

- [ai-eval-harness](https://github.com/prasanth2006z/ai-eval-harness): the shared evaluation harness used to measure every case (retrieval hit rate, access-control leaks, latency, refusals and citations).

## How the repositories are organised

See [ADR-000](adr/ADR-000-repository-structure.md).

## Notes

All data is synthetic. Companies, policies and people in the cases are fictional.
