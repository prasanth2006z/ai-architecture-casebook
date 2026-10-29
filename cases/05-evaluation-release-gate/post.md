# Evaluation as a Release Gate: No Change Ships Without a Score

*A design case study: how a one-line prompt change broke an HR assistant for nine days, and the release gate that would have stopped it in fifteen minutes.*

![Cover](images/00-cover.png)

*Part of the AI Architecture Casebook: real-world AI problems, redesigned one decision at a time.*

> **About this case study.** This is a composite scenario built on synthetic data. It shows a design and how to measure it. The numbers are planning figures, not benchmark results.

---

## The problem

Case 01 built an HR policy assistant on AWS. Employees in several countries ask it about leave, benefits and travel, and it answers from the policies they are allowed to see, citing the section it used. Access is decided by data, never by the model.

The assistant went live and people liked it. Then the changes started. In six weeks the team:

- upgraded the model version,
- changed the chunk size for one policy set,
- loaded a new batch of policies for two countries,
- and edited the prompt three times.

Each change was small. None was tested in a repeatable way, because each one felt like configuration, not code.

The third prompt edit was meant to make answers shorter and friendlier. It shipped on a Friday afternoon.

![Nine days between a one-line change and anyone noticing.](images/01-the-friday-change.png)
*Nine days between a one-line change and anyone noticing.*

The shorter prompt dropped two sentences. One asked the model to cite the section it used. The other said: *if no policy for the employee's country is in the context, say so and point them to HR.*

Over the next week, citations fell from almost every answer to about six in ten. Worse, an employee in Germany asked about parental leave. The German policy wasn't in the retrieved context for that question, so the assistant answered from the UK policy, confidently and without a citation. Nobody noticed until HR got a complaint on day nine.

Two reactions came up:

- **"Freeze the prompt."** The assistant still needs to improve. Freezing it doesn't make it safe, just stale.
- **"Test more carefully."** By hand, before every change? That lasts about two releases.

The real problem was simpler:

> **A prompt change is a release.** Every release gets a score, compared with the version it replaces, before it reaches users.

## What the fix had to satisfy

![The first two rows cannot bend.](images/t1-requirements.png)
*The first two rows cannot bend.*

## Decision 1: Everything that changes behaviour ships as one bundle

The first question was: *what counts as a change?* The answer is anything that can change an answer.

![Six things can change an answer. They are versioned and released together.](images/02-what-counts-as-a-change.png)
*Six things can change an answer. They are versioned and released together.*

These six things are now described in one file, the **release bundle**, kept in git:

```yaml
bundle: hr-assistant-2026-10-24.1
model: <bedrock model id, pinned>
inference: {temperature: 0.2, max_tokens: 700}
prompt: prompts/answer.v14.md
retrieval:
  knowledge_base: hr-policies
  data_snapshot: 2026-10-22
  chunking: section-v3
  top_k: 8
guardrail: hr-guardrail:7
```

Two rules come with it:

1. **Production runs exactly one bundle.** Its ID is written into every log line and trace, so any answer can be traced to the exact prompt, model and data that produced it.
2. **Nothing can change outside a bundle.** Prompts are not editable in a console in production. A data load creates a new snapshot, and the snapshot only becomes live through a new bundle.

This is the least exciting decision and the one everything else depends on. You can't compare two versions if you can't name them.

## Decision 2: A golden set in three parts

A golden set is a list of questions with known good behaviour. Ours has about 250 items, built from real (anonymised) questions, and split into three parts with different jobs.

![Three parts, three jobs. Prompt authors never see the hold-out.](images/t2-golden-set.png)
*Three parts, three jobs. Prompt authors never see the hold-out.*

Each item records more than a question and an answer:

```yaml
id: GS-0412
question: "How much parental leave do I get?"
user: {country: DE, grade: L4}
expect:
  behaviour: answer          # or: refuse
  section: DE-PAR-2.1        # must be cited
  facts:
    - "20 weeks at full pay" # synthetic
  must_not_cite_country: [UK, US]
```

The user profile matters as much as the question. The same question from an employee in Germany and one in the UK has two different correct answers. The Friday change would have failed a dozen items like this one.

**Every incident adds items.** The German parental-leave case is now in the must-pass set, along with four variations of it.

## Decision 3: Deterministic checks first, a judge model second

Not every question about an answer needs a model to grade it.

![Use exact checks where the answer is known. Use a judge only for what needs judgement.](images/03-three-layers.png)
*Use exact checks where the answer is known. Use a judge only for what needs judgement.*

**Layer 1: deterministic checks.** No model involved, so the same input always gives the same score.

- **Retrieval:** did the expected section appear in the top 8 results?
- **Citation:** does the answer cite a section, and is that section one of the retrieved ones?
- **Leaks:** did any retrieved document fall outside the user's entitlements? This must be zero, and it is checked against the entitlement data, never by asking a model. That's the rule from Case 01.
- **Behaviour:** the assistant returns a structured field, `answered` or `referred_to_hr`. If the item expects a refusal, the check reads that field.
- **Country:** the answer must not cite a policy from another country.

**Layer 2: a judge model**, for what has no exact answer:

- **Faithfulness:** is every claim supported by the retrieved text?
- **Correctness:** does the answer contain the item's key facts?
- **Completeness** and **clarity.**

We use Amazon Bedrock's evaluation jobs for this (they support RAG evaluation with an LLM as judge and custom metrics), but a small harness of your own works too. Three rules apply to the judge:

1. **Pin the judge model version.** A judge upgrade is its own release, with its own comparison.
2. **Calibrate it.** About 100 answers were labelled by HR, and we check that the judge agrees with them before trusting its scores.
3. **Measure its noise.** Run the judge three times on the current production bundle. The spread between runs is the noise band, and a score has to move further than that to count.

**Layer 3: people**, only for high-risk changes. A model upgrade or a new country gets 20 answers reviewed by someone from HR before release.

## Decision 4: Gate on the baseline, not on a magic number

A release passes or fails by comparing it with production, not against a fixed target.

![Hard gates are absolute. Soft gates compare with production.](images/t3-gate-rules.png)
*Hard gates are absolute. Soft gates compare with production.*

- **Hard gates** never bend: zero leaks, 100% on the must-pass set.
- **Soft gates** compare with the current production bundle, run on the same day with the same judge. A metric may not drop by more than its noise band plus a small tolerance.
- **Hold-out:** the hold-out score must move in the same direction as the core score. If core goes up and hold-out goes down, the change is tuned to the questions, not to the problem.

The result is one of three: **pass**, **fail**, or **needs review**. "Needs review" means a soft gate failed and the owner can still ship, but only by writing down why, in the pull request. Overrides are counted. If they become routine, the gate is wrong and needs fixing, not ignoring.

Here is what the gate would have said about the Friday change:

![The gate would have stopped the Friday change in about fifteen minutes.](images/04-gate-report.png)
*The gate would have stopped the Friday change in about fifteen minutes.*

## Decision 5: The gate runs in the pipeline, and again in production

![Offline gate on every pull request, then a canary with online evaluation.](images/05-pipeline.png)
*Offline gate on every pull request, then a canary with online evaluation.*

**Before merge.** A pull request that changes the bundle starts a CodeBuild job. It runs the golden set through the candidate bundle and the production bundle, scores both, and posts the report on the pull request. A full run is about 250 questions and around 1,000 model calls, and takes about fifteen minutes.

**After merge.** The assistant runs on Lambda, and the bundle ID is part of the deployment. CodeDeploy shifts 10% of traffic to the new version first. During the canary, a sample of real conversations is scored with the same deterministic checks and judge. If you host the assistant on Amazon Bedrock AgentCore, AgentCore Evaluations can do this online scoring for you; otherwise a small sampler does the same job. If the leak check fires, or the online scores fall below the baseline, an alarm rolls the deployment back automatically.

The offline gate catches what we can imagine. The canary catches what real users do that we didn't.

## A sketch of the gate

```python
def gate(cand, prod, noise, tol=0.01):
    # Hard gates: absolute.
    if cand["leaks"] > 0:
        return "fail", ["leak"]
    if cand["must_pass"] < 1.0:
        return "fail", ["must_pass"]

    # Soft gates: relative to production.
    issues = []
    for m in SOFT_METRICS:
        drop = prod[m] - cand[m]
        if drop > noise[m] + tol:
            issues.append(f"{m} -{drop:.2f}")

    # Hold-out must move with core.
    if (cand["core"] > prod["core"]
            and cand["holdout"] < prod["holdout"]
                - noise["holdout"]):
        issues.append("overfit")

    if issues:
        return "needs_review", issues
    return "pass", []
```

Notice what's missing: no line says "if the score is above 0.8, ship". There is no magic number. The question is always *is it worse than what we have now?*

## What can still go wrong

![What can still go wrong, and how you would catch it.](images/t4-risks.png)
*What can still go wrong, and how you would catch it.*

The number to watch is the gate's **catch rate**: of the problems found in production, how many would the gate have caught? Each production incident answers that question once, and then becomes a test.

**At 10x**, I'd expect these to change first:

- With many assistants, the harness and judge become a shared platform service, owned by one team.
- A golden set of thousands of items makes every run expensive. Run a stratified sample on each pull request, and the full set nightly and before production.
- Judge cost and drift become a line item. Re-calibrate against people every quarter.

## What we would do differently

- **Version the prompt on day one.** The bundle was harder to introduce after six weeks of console edits.
- **Collect refusals as carefully as answers.** The most dangerous failure was an answer that should have been a refusal.
- **Ask HR to own the must-pass set.** Engineers wrote the first version; HR knew which mistakes mattered.

## Key takeaways

1. **A prompt change is a release.** Version the model, prompt, retrieval settings, data and guardrails together, and log the bundle ID with every answer.
2. **Build the golden set from real questions, and include the user.** The same question can have different correct answers for different people.
3. **Use exact checks where the answer is known,** and a pinned, calibrated judge only for what needs judgement. Never let a model decide whether data leaked.
4. **Gate on the baseline, not a magic number.** Hard gates for safety, relative gates for quality.
5. **Keep a hold-out set** so a change can't be tuned to the test.
6. **Run the gate again in production** with a canary and automatic rollback.

---

*Next in the series: Case 06, a support agent that can issue refunds (AWS). The design and decision records for this case are in the [series repository](https://github.com/prasanth2006z/ai-architecture-casebook/tree/main/cases/05-evaluation-release-gate).*

*How would you have handled it? I'd like to hear other approaches in the comments.*

*AWS details reflect public documentation as of October 2026. Check current docs before you build.*
