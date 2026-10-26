# An LLM Gateway That Cut the Bill: Meter First, Then Route

*A design case study: why a growing model bill is usually a routing and caching problem, and how one small gateway made it visible and then smaller.*

![Cover](images/00-cover.png)

*Part of the AI Architecture Casebook: real-world AI problems, redesigned one decision at a time.*

> **About this case study.** This is a composite scenario. The apps, teams and numbers are illustrative. It shows a design and how to measure it. The numbers are planning figures, not benchmark results.

---

## The problem

A mid-sized company has nine internal apps that call Gemini models. A claims summariser, a support-ticket classifier, a contract Q&A tool, a nightly enrichment job, two agents, and a few smaller tools. Each team set up its own access: some use a service account, two use API keys, one shares a key with another team.

In January the monthly model bill was about $11,000. In September it was about $48,000.

![The bill quadrupled in nine months, and nobody could say which app caused it.](images/01-the-bill.png)
*The bill quadrupled in nine months, and nobody could say which app caused it.*

Finance asked a simple question: *which team is spending this, and on what?* Nobody could answer. Every call landed in the same Google Cloud project. The bill showed models and token counts, not apps or features.

Two answers came up straight away:

- **"Switch everyone to the cheapest model."** That would cut the bill and break the two use cases that really need a stronger model.
- **"Negotiate a discount."** A discount on waste is still waste.

Both skip the first step. The real problem was simpler:

> **You can't cut a bill you can't attribute.** Meter every call first. Then route each use case to the cheapest model that passes its evaluation, and cache what repeats.

## What the fix had to satisfy

![The first two rows cannot bend.](images/t1-requirements.png)
*The first two rows cannot bend.*

The first row matters most. A cheaper model that quietly gives worse answers is not a saving; it is a cost moved somewhere harder to see.

## The design in one picture

![Every model call goes through one gateway, which meters, limits, routes and caches.](images/02-architecture.png)
*Every model call goes through one gateway, which meters, limits, routes and caches.*

The gateway is a small service on Cloud Run. Apps call it instead of calling the model directly. It looks up the caller's **use case**, checks the budget, applies caching, calls the model the use case is configured for, and writes a usage record to BigQuery.

Models are reached through Google's Gemini Enterprise Agent Platform, formerly Vertex AI. The rename happened in April 2026, and the `aiplatform.googleapis.com` endpoint stays the same.

Six decisions carry the design.

## Decision 1: One door to the models

The first step is boring and does most of the work: **every model call goes through the gateway, and nothing else can call the models.**

- Only the gateway's service account has permission to call models in the project. Teams' own service accounts lose it, and the API keys are revoked.
- Each app calls the gateway with its own identity (an ID token from its service account). The gateway never trusts a team name written in the request body.
- Each request names a **use case**, such as `claims-summary` or `nightly-enrichment`. A use case is the unit of ownership, budget and routing. The gateway checks that the caller is allowed to use it.

We looked at four ways to build the door:

![Four ways to put a door in front of the models.](images/t2-gateway-options.png)
*Four ways to put a door in front of the models.*

If you already run Apigee, its LLM token policies (token quotas per app and prompt-size limits) and its semantic-cache support cover a lot of this design, and that is a reasonable choice. We didn't run Apigee, and the gateway needed to do only five things, so we kept our own on Cloud Run. It is a few hundred lines, and it's the most-tested code in the system.

## Decision 2: Meter every call before changing anything

For the first two weeks the gateway changed nothing. It passed every call through and wrote one record per call:

```
time, caller, use_case, owner_team,
model, mode (online | batch),
input_tokens, cached_tokens, output_tokens,
latency_ms, status, retry_of,
cache_layer, cost_usd, price_version
```

Cost is computed from a **versioned price table** in the gateway's config, so a record always says which prices it used. It won't match the invoice to the cent, and it doesn't need to. It has to be close enough to rank use cases, and the monthly total is reconciled against the billing export.

Two weeks of records answered finance's question:

![Where the September bill went, by cause.](images/03-where-the-money-went.png)
*Where the September bill went, by cause.*

None of the five causes was "the model is too expensive". They were:

1. **The strongest model for everything.** Every app defaulted to a Pro-class model, including classification and short extraction, where a Flash-class model passed the same tests.
2. **The same long prompt, sent again and again.** The contract Q&A tool sent a 7,000-token policy pack with every question, but it put the user's question first, so the shared part never formed a reusable prefix.
3. **A nightly job paying on-demand prices.** The enrichment job had no deadline tighter than "by morning", yet it called the online API row by row.
4. **Retries and one runaway.** One weekend, an agent retried a failing tool call in a loop for 31 hours.
5. **Duplicate work.** Three apps summarised the same incoming documents.

## Decision 3: Route by use case, not by request

The obvious fix for cause 1 is a "smart router": a small model that reads each request and picks a model. We didn't do that. A per-request router adds a model call to every request, and it makes quality depend on a classifier nobody evaluates.

Instead, **each use case is configured with a model tier**, and the tier only changes when the evaluation says so.

![Each use case has a tier. Moving it to a cheaper one needs a passing evaluation.](images/04-route-by-use-case.png)
*Each use case has a tier. Moving it to a cheaper one needs a passing evaluation.*

The config lives in git, next to the gateway:

```yaml
claims-summary:
  owner: claims-team
  tier: flash
  max_output_tokens: 800
  budget_usd_per_day: 120
  on_budget: alert
contract-qa:
  owner: legal-ops
  tier: pro
  budget_usd_per_day: 300
  on_budget: alert
nightly-enrichment:
  owner: data-team
  tier: flash-lite
  mode: batch
  budget_usd_per_day: 60
  on_budget: stop
```

Tiers are names, not model IDs. The gateway maps `flash` to a specific, pinned model version. Upgrading a tier is a config change, and it goes through the same evaluation gate as a prompt change. That gate is Case 05.

To move a use case down a tier, its owner runs its golden set (a few dozen real requests with expected results) against both tiers. If the cheaper tier is within the agreed margin, the config changes. In this scenario, six of the nine use cases moved down. Contract Q&A and one agent stayed on Pro.

## Decision 4: Cache in layers, and never across users

Caching is the second-largest saving, and the easiest one to get wrong. We use three layers, from safest to riskiest.

![Three layers of caching, from safest to riskiest.](images/05-cache-layers.png)
*Three layers of caching, from safest to riskiest.*

**Layer 1: prompt prefix caching.** Gemini models on the platform reuse a repeated prompt prefix and bill the cached tokens at a reduced rate. This is implicit caching, and it only helps if the stable part comes first. So the gateway requires prompts in a fixed order: system instructions, then shared documents, then the user's input. For the contract Q&A tool, moving the question to the end turned most of each prompt into a cached prefix. For a large document used all day, an explicit cache with a time-to-live is worth it too.

**Layer 2: an exact-response cache.** For use cases that are deterministic (temperature 0, same input gives the same output), the gateway caches the response under a hash of the model version, the full prompt, the parameters and the **data version** of anything the prompt was built from. The same document summarised by three apps now costs one call. The data version is what keeps this safe: when the document changes, the key changes.

**Layer 3: a semantic cache, off by default.** A semantic cache returns a stored answer for a question that is *similar* to an earlier one. It saves more, and it can return the wrong answer with complete confidence. We allow it only for public, non-personal content, such as an internal FAQ. **It is never allowed for anything filtered by user permissions.** Two users with different access can ask the same question and deserve different answers. That is the rule from Case 01: access is decided by data, and a cache must not become a way around it.

**Batch, for work that can wait.** The nightly enrichment job now submits one batch job instead of 40,000 online calls. Batch inference is billed at a discount and doesn't use the online quota the interactive apps depend on.

## Decision 5: Budgets that stop runaways, not users

Every use case has a daily budget. What happens when it is reached depends on who is calling.

![What happens at the budget depends on who is calling.](images/t3-budget-behaviour.png)
*What happens at the budget depends on who is calling.*

- **Interactive apps alert; they don't stop.** Cutting off a claims handler mid-shift costs more than the tokens. The owner is paged at 80% and 100%.
- **Agents and batch jobs stop.** Nobody is waiting on them in real time, and they are where runaways happen.
- **Retries have their own budget.** The gateway allows two retries with backoff. If the same use case sends the same failing request ten times in a minute, the gateway opens a circuit breaker for that use case and pages the owner.

The 31-hour weekend loop would have been stopped within a minute by the circuit breaker, and at the latest by the daily budget.

## Decision 6: Keep the gateway boring

The gateway sits on the path of every AI feature in the company, so it has to be dull and reliable.

- **It never rewrites prompts.** It may reject a request (too large, wrong order, over budget), but it never edits one. Teams must be able to trust that what they send is what the model sees.
- **No automatic model fallback.** If a model is unavailable, the gateway returns an error. A fallback is allowed only if it is listed in the use case's config and passed that use case's evaluation. Silent fallbacks are silent quality changes.
- **Metering never blocks a request.** Usage records go through Pub/Sub to BigQuery. If BigQuery is slow, requests still flow and records catch up.
- **Budget checks fail open for interactive use cases, closed for agents and batch.** If the budget counter store is unavailable, an interactive call goes through and is logged; an agent call waits.
- **Stateless and regional.** Several instances, a minimum instance count so there are no cold starts, and timeouts set per use case.

## A sketch of the gateway

```python
def handle(req, caller):
    uc = POLICIES[req.use_case]  # from git
    if caller not in uc.callers:
        raise Forbidden(req.use_case)

    check_prompt_order(req, uc)
    budget.check(uc)  # stops agents and batch

    key = None
    if uc.exact_cache:
        key = cache_key(uc, req)
        hit = cache.get(key)
        if hit:
            record(req, uc, hit, layer="exact")
            return hit

    resp = call_model(
        model=TIERS[uc.tier],  # pinned version
        prompt=req.prompt,
        max_output_tokens=uc.max_output,
        timeout=uc.timeout_s,
        retries=uc.max_retries,
    )

    if key:
        cache.set(key, resp, ttl=uc.cache_ttl)
    budget.add(uc, resp.usage)
    record(req, uc, resp, layer="none")
    return resp


def cache_key(uc, req):
    return sha256(json.dumps({
        "model": TIERS[uc.tier],
        "prompt": req.prompt,
        "params": req.params,
        "data_version": req.data_version,
    }, sort_keys=True).encode()).hexdigest()
```

Notice what's missing: no line decides which model to use by reading the request. The use case decides, and the evaluation decides the use case.

## What it saved

![From about $48,000 to about $20,000 a month. Most of it came from routing, not discounts.](images/06-savings.png)
*From about $48,000 to about $20,000 a month. Most of it came from routing, not discounts.*

The biggest saving came from the least technical change: moving six use cases to a cheaper tier after their evaluations passed. Caching came second. Stopping the runaway was small in a normal month and large in a bad one.

## What can still go wrong

![What can still go wrong, and how you would catch it.](images/t4-risks.png)
*What can still go wrong, and how you would catch it.*

The number to watch is **cost per successful task**, per use case, not the total bill. The total goes up when usage grows, which is fine. Cost per task going up means something changed: a longer prompt, a tier change, a cache that stopped hitting.

**At 10x**, I'd expect these to change first:

- With many more use cases, the policy file needs an owner and a review process of its own, not just a pull request.
- Provisioned throughput becomes worth pricing for the two or three steadiest interactive use cases.
- If most traffic becomes agents calling tools, Agent Platform's Agent Gateway is worth evaluating for agent-to-tool traffic. This gateway still covers agent-to-model calls.

## What we would do differently

- **Turn on metering first, on day one of the first AI app.** Attribution is cheap to add early and painful to reconstruct later.
- **Make "use case" a required field from the start.** Retrofitting it meant reading nine codebases.
- **Write the golden set before choosing the model.** Every tier change in this case waited on an owner writing tests.

## Key takeaways

1. **You can't cut a bill you can't attribute.** Put one door in front of the models and meter every call.
2. **Route by use case, not by request.** Each use case gets a tier, and the tier changes only when its evaluation passes.
3. **Put the stable part of the prompt first.** Prefix caching only works if there is a prefix.
4. **Cache exact responses with a data version, and never cache across users.** A semantic cache must not bypass permissions.
5. **Stop runaways, not users.** Agents and batch jobs hit a hard budget; interactive apps alert.
6. **Keep the gateway boring.** It never rewrites prompts and never silently falls back.

---

*Next in the series: Case 05, evaluation as a release gate (AWS). The design and decision records for this case are in the [series repository](https://github.com/prasanth2006z/ai-architecture-casebook/tree/main/cases/04-llm-gateway).*

*How would you have handled it? I'd like to hear other approaches in the comments.*

*Google Cloud details reflect public documentation as of October 2026. Check current docs and pricing before you build.*
