# AI Architecture Casebook

Real-world AI problems worked through the way an architect would: requirements, options, trade-offs, decisions and how to prove the result works. Each case is a mocked but realistic problem on AWS or GCP, with a design document and Architecture Decision Records (ADRs).

The series is published on Medium. Start with the introduction: [Designing AI Systems with an API Mindset](https://medium.com/@prasanth_pattathil/51131e78a179)

## Cases

| # | Case | Cloud | Medium post | Design and ADRs |
|---|------|-------|-------------|-----------------|
| 01 | Permission-aware RAG for HR policies | AWS | [Designing a RAG System That Knows What You're Allowed to See](https://medium.com/@prasanth_pattathil/7ac66c3f81eb) | [cases/01-permission-aware-rag](cases/01-permission-aware-rag) |
| 02 | Invoice extraction with human review | AWS | [Invoice Extraction with Human Review: Route on Checks, Not on Confidence](https://medium.com/@prasanth_pattathil/177496bc2f98) | [cases/02-invoice-extraction](cases/02-invoice-extraction) |
| 03 | Keeping a team knowledge assistant in sync | GCP | [Keeping a Team Knowledge Assistant in Sync: Index on Change, Retrieve on Question](https://medium.com/@prasanth_pattathil/768768228575) | [cases/03-knowledge-assistant-sync](cases/03-knowledge-assistant-sync) |
| 04 | An LLM gateway that cut the bill | GCP | [An LLM Gateway That Cut the Bill: Meter First, Then Route](https://medium.com/@prasanth_pattathil/25837692664d) | [cases/04-llm-gateway](cases/04-llm-gateway) |
| 05 | Evaluation as a release gate | AWS | [Evaluation as a Release Gate: No Change Ships Without a Score](https://medium.com/@prasanth_pattathil/496eee59cbde) | [cases/05-evaluation-release-gate](cases/05-evaluation-release-gate) |
| 06 | A support agent that can issue refunds | AWS | [A Support Agent That Can Issue Refunds: The Model Proposes, the Customer Confirms](https://medium.com/@prasanth_pattathil/c77debe2a12f) | [cases/06-refund-agent](cases/06-refund-agent) |
| 07 | A loop agent that upgrades 300 repositories | GCP | [A Loop Agent That Upgrades 300 Repositories: The Loop Is Code, the Model Is One Step](https://medium.com/@prasanth_pattathil/ced6fee10e2b) | [cases/07-loop-agent-upgrades](cases/07-loop-agent-upgrades) |
| 08 | Memory for an account-manager assistant | AWS | [Memory for an Account-Manager Assistant: Every Memory Needs an Owner, a Source and an Expiry](https://medium.com/@prasanth_pattathil/625a1b83747b) | [cases/08-account-manager-memory](cases/08-account-manager-memory) |
| 09 | One agent or five? A research assistant | GCP | [One Agent or Five? A Research Assistant: Split Only When It Buys You Something](https://medium.com/@prasanth_pattathil/b46945b783e7) | [cases/09-one-agent-or-five](cases/09-one-agent-or-five) |

Cases 03–09 publish weekly on Mondays from November 2 to December 14, 2026. Their Medium links work once each post is live.

## Related repositories

- [ai-eval-harness](https://github.com/prasanth2006z/ai-eval-harness): the shared evaluation harness used to measure every case (retrieval hit rate, access-control leaks, latency, refusals and citations).

## How the repositories are organised

See [ADR-000](adr/ADR-000-repository-structure.md).

## Notes

All data is synthetic. Companies, policies and people in the cases are fictional.
