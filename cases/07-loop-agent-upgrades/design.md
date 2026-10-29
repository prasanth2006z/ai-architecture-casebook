# Case 07: A Loop Agent That Upgrades 300 Repositories

**Cloud:** Google Cloud · **Status:** Design (ADRs proposed), post ready · **Blog post:** *A Loop Agent That Upgrades 300 Repositories: The Loop Is Code, the Model Is One Step* (`post.md`)

> Composite scenario. Services, numbers and timings are illustrative planning figures.
> Model calls go through the Case 04 gateway; agent changes are reviewed like Case 05 releases.

![Cover](images/00-cover.png)

## 1. Problem

~300 Node.js services, most on Node.js 20 (end-of-life April 30, 2026). Target: Node.js 24 by year end. Manual effort: half a day to two days per repo (~1 engineer-year); platform team of four.

Pilot (20 repos, instructions "Upgrade to Node.js 24. Make CI green. Open a pull request."):
- 14 green; in 5 the agent changed tests (removed assertions, `.skip`), in 2 it edited CI to skip lint, in 1 it downgraded a dependency to a vulnerable version.
- 3 runs looped ~40 iterations (~6 hours each).
- 1,800-line mixed diffs; reviewers rubber-stamped or ignored them.
- No state; crashes restarted from scratch.

**Core problem:** the model decided when it was done and could edit the thing that judged it. The loop must be code, and the verifier must be outside the model's reach.

![Pilot](images/01-pilot.png)

## 2. Requirements

![Requirements](images/t1-requirements.png)

**Must never go wrong**
- No weakened tests, CI or lint configuration.
- No dependency downgrades.

**Functional**
- All services on Node.js 24 by year end; progress visible by team.
- Reviewable pull requests (script vs agent commits, reasons per file).
- Useful escalations (what changed, what was tried, last error).

**Non-functional**
- Bounded cost/time per repo (5 iterations, budget, 45 minutes).
- Fleet pausable and resumable; idempotent steps.
- Verifier isolated from production credentials.

**Out of scope:** framework major upgrades (same machinery, later); behaviour changes not covered by tests.

## 3. Architecture

![Architecture](images/02-architecture.png)

```
Cloud Run job (one task per repo, max 20 concurrent)
  └─ per repo, reading/writing Firestore state:
       1. upgrade script → commit 1 → verifier (Cloud Build, isolated project)
            green → PR (script-only)
       2. coverage < 40% → escalate (no agent)
       3. agent loop (ADK + Gemini via Case 04 gateway), max 5 iterations:
            propose → diff guard (code) → verifier
            loop code: green → PR (script + agent commits)
                       same error twice / budget / 5 iterations → escalate with note
```

| Component | Google Cloud service | Responsibility |
|---|---|---|
| Fleet runner | Cloud Run jobs (tasks) | One task per repo; concurrency cap |
| Fleet state | Firestore | Status, attempts, test counts, PR URL per repo |
| Upgrade script | Container in the job | Version bumps, lockfile, codemods |
| Agent | ADK (`LoopAgent` or ADK 2.0 graph workflow) + Gemini via Case 04 gateway | Propose fixes for remaining failures |
| Diff guard | Code in the job | Reject weakened tests, protected files, downgrades, large diffs |
| Verifier | Cloud Build in an isolated project | Install, build, lint, unit tests, container build, smoke test |
| Source | Git hosting API | Branches, commits, pull requests |
| Dashboard | Looker Studio on Firestore export / BigQuery | Progress by team and wave |

## 4. Key decisions

| ADR | Decision |
|---|---|
| [ADR-001](adr/ADR-001-script-first-agent-for-remainder.md) | Deterministic script first; the agent only works on remaining failures |
| [ADR-002](adr/ADR-002-verifier-and-diff-guard-outside-agent.md) | Verifier and diff guard outside the agent; "done" = guard + verifier pass |
| [ADR-003](adr/ADR-003-bounded-loop-with-escalation.md) | Loop bounded in code (iterations, no-progress, budget, time); escalate with a note |
| [ADR-004](adr/ADR-004-fleet-as-resumable-jobs.md) | Fleet runs as resumable jobs with per-repo state |
| [ADR-005](adr/ADR-005-waves-exclusions-merge-policy.md) | Waves with gates, low-coverage exclusion, human review for agent changes |

![Guard rules](images/t2-guard-rules.png)
![The loop](images/03-the-loop.png)

## 5. Repo state record

```
repo, owner_team, wave, risk, status (queued|script|agent|pr_open|merged|escalated|excluded),
script_commit, agent_iterations, last_error, tests_before, tests_after, pr_url, updated_at
```

## 6. Rollout

![Waves](images/04-waves.png)
![PR template](images/t3-pr-template.png)

## 7. Planning numbers

![Outcomes](images/05-outcomes.png)

| Outcome | Repos |
|---|---|
| Script only, green | 190 (63%) |
| Script + agent, green within 5 iterations | 74 (25%) |
| Escalated: low coverage (agent not run) | 22 |
| Escalated: agent gave up | 14 |
| Agent changes rejected by reviewers | ~1 in 12 |

## 8. Risks

![Risks](images/t4-risks.png)

## 9. At 10x

- Script gets its own test suite and release process.
- Reserve CI capacity.
- Keep loop and guard generic; swap script and instructions per migration.

## 10. Open questions

- Coverage threshold for agent eligibility (40% assumed).
- Owner opt-in for auto-merge of script-only PRs.
- Whether payment-path services get the agent at all.
