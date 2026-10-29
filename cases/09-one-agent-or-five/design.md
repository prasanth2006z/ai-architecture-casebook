# Case 09: One Agent or Five? A Research Assistant

**Cloud:** Google Cloud · **Status:** Design (ADRs proposed), post ready · **Blog post:** *One Agent or Five? A Research Assistant: Split Only When It Buys You Something* (`post.md`)

> Composite scenario. Team, questions and numbers are illustrative planning figures.
> Links to Case 05 (task set as release gate), Case 04 (model calls via gateway). Instructions hidden in fetched content are left for a later post.

![Cover](images/00-cover.png)

## 1. Problem

A strategy team writes competitor briefs ("How has Competitor X changed pricing in the last 12 months? With sources."). ~2 analyst-days per brief by hand.

First design: five agents (planner, searcher, reader, analyst, writer) in a shared conversation. On 40 past questions with reference briefs: ~14× the cost of one agent, ~6 minutes per brief, 1 in 5 briefs cited a source never retrieved, and failures couldn't be attributed to a step. A single agent was cheap and fast but lost recall on broad, many-source questions as its context filled.

**Core problem:** agents were added to mirror job titles, not for a measurable benefit; hand-offs were prose; citations were trusted, not checked.

![Five agents](images/01-five-agents.png)

## 2. Requirements

![Requirements](images/t1-requirements.png)

**Must never go wrong**
- Every citation points to a page fetched in this run.
- Every cited quote appears verbatim in that stored page.

**Functional**
- High key-fact recall, including broad questions.
- Failed citation checks visible in an "Unverified" section.

**Non-functional**
- Max 12 sources and a token budget per brief.
- Every step's input and output stored for debugging.

**Out of scope:** licensed/paywalled sources (later, separate reader), automated publishing of briefs.

## 3. Architecture

![Architecture](images/02-architecture.png)

```
Question ─► Plan (1 call) ─► Search (Google Search grounding + internal library) ─► code picks ≤ 12 sources
         ─► fetch + store pages (Cloud Storage)
         ─► Readers in parallel (1 per source, clean context, no tools) ─► typed notes
         ─► Write from notes only (cites note IDs) ─► Verify citations (code) ─► Brief + "Unverified"
```

| Component | Google Cloud service | Responsibility |
|---|---|---|
| Workflow | Cloud Run service; ADK sequential workflow with a parallel step (or ADK 2.0 graph workflow) | Fixed order, limits, budgets |
| Models | Gemini on Gemini Enterprise Agent Platform (formerly Vertex AI), via Case 04 gateway | Plan, read, write |
| Search | Grounding with Google Search; internal research library search | Candidate sources |
| Fetch + store | Cloud Run + Cloud Storage | Fetch pages; store text as seen |
| Notes and runs | Firestore | Notes, step inputs/outputs per run |
| Verifier | Code in the workflow | Citation checks |
| Evaluation | Cloud Run job | 40-question task set; recall judge; citation counts |

## 4. Key decisions

| ADR | Decision |
|---|---|
| [ADR-001](adr/ADR-001-split-only-for-measured-reasons.md) | One agent by default; split only for parallel work, clean context or a different permission |
| [ADR-002](adr/ADR-002-workflow-in-code.md) | Fixed workflow in code with limits; agents don't chat |
| [ADR-003](adr/ADR-003-parallel-readers-typed-notes.md) | Parallel readers with isolated contexts return typed notes; writer cites note IDs |
| [ADR-004](adr/ADR-004-citations-verified-by-code.md) | Citations verified by code against stored pages; failures shown as "Unverified" |
| [ADR-005](adr/ADR-005-choose-architecture-with-task-set.md) | Architecture choices decided on a task set, re-run on model or framework changes |

![When to split](images/t2-when-to-split.png)
![Notes](images/03-notes.png)
![Citation check](images/04-citation-check.png)

## 5. Note schema

```
note_id, run_id, source_id (assigned by code), quote (verbatim), claim, about_date, created_at
```

## 6. Planning numbers

![Comparison](images/t3-comparison.png)

| | Single agent | Five agents | Hybrid |
|---|---|---|---|
| Key-fact recall | 0.71 | 0.74 | 0.83 |
| Recall, broad questions | 0.58 | 0.69 | 0.81 |
| Citation errors reaching analyst | 6% | 21% | 0% (2% sentences marked unverified) |
| Cost per brief | ~$0.40 | ~$5.60 | ~$1.10 |
| Time per brief | ~2.1 min | ~6.3 min | ~1.6 min |

## 7. Risks

![Risks](images/t4-risks.png)

## 8. At 10x

- Shared, de-duplicated page store with retention policy.
- Licensed sources behind their own reader and credentials.
- Task set becomes a release gate (Case 05).

## 9. Open questions

- Quote normalisation rules (whitespace, punctuation, PDFs).
- Domain block-list ownership.
- Retention of stored pages (copyright and storage).
