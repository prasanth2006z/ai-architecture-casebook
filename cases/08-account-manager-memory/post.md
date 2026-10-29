# Memory for an Account-Manager Assistant: Every Memory Needs an Owner, a Source and an Expiry

*A design case study: why "remember everything I told you" turned into leaked discounts and stale contacts, and how to design memory as data.*

![Cover](images/00-cover.png)

*Part of the AI Architecture Casebook: real-world AI problems, redesigned one decision at a time.*

> **About this case study.** This is a composite scenario built on synthetic data. Companies, people and numbers are invented. It shows a design and how to measure it. The numbers are planning figures, not benchmark results.

---

## The problem

A B2B company that sells service contracts for industrial equipment has about 60 account managers. Each one looks after around 40 customer accounts.

The team uses an assistant to prepare for customer calls. Before a meeting with Acme, an account manager asks it for a briefing: open opportunities from the CRM, recent support tickets, the last few emails, and what happened at the last meeting.

The most requested feature was simple: **"remember what I tell you."** Acme's CFO is new. Their operations lead hates long slide decks. They're quietly evaluating a competitor. None of that lives in the CRM, and account managers were tired of repeating it.

The first version of memory was just as simple. Every conversation was stored, per account manager, and the last 30 conversations were loaded into the context at the start of each session.

It worked for about a month. After three months, this is what the team had found:

![What "remember everything" did after three months.](images/01-what-went-wrong.png)
*What "remember everything" did after three months.*

1. **One customer's discount showed up in another customer's briefing.** Preparing for Globex, the assistant mentioned "the 18% discount we discussed". That was Acme. Both accounts were in the same account manager's history, and the model blended them.
2. **A contact who had left was still the champion.** "Priya Shah is your champion at Acme." She left two months ago. The CRM was updated; the memory wasn't.
3. **Something personal was kept, and travelled.** An account manager once mentioned that a contact's husband was in hospital, as a reason to go easy on a deadline. The assistant kept it and included it in a briefing that was later forwarded to a colleague.
4. **Knowledge left with people.** When an account manager moved on, the next one started from nothing, because memory belonged to the person, not the account.
5. **Sessions got slow and expensive.** Thirty transcripts were about 60,000 tokens per session, most of them irrelevant to the account in question.

None of this was the model misbehaving. It was a design that treated memory as a pile of transcripts instead of as data.

> **Memory is data.** Every memory needs an owner, a scope, a source and an expiry, and the system of record always wins.

## What the fix had to satisfy

![The first three rows cannot bend.](images/t1-requirements.png)
*The first three rows cannot bend.*

## Decision 1: Different kinds of memory, with different scopes

"Memory" was really four different things with different owners and lifetimes.

![Four kinds of memory. The scope decides who can ever see it.](images/t2-memory-types.png)
*Four kinds of memory. The scope decides who can ever see it.*

- **The current session** belongs to the conversation and expires after 30 days.
- **My preferences** ("bullet points, not paragraphs", "I'm in Lisbon") belong to the account manager and nobody else.
- **Account notes** ("the CFO is new since September", "evaluating a competitor") belong to the **account**, and the account team can see them.
- **Meeting summaries** belong to the account too, with the date and who was there.

This design uses Amazon Bedrock AgentCore Memory. It keeps short-term memory (the raw events of a session) and long-term memory, where built-in strategies extract preferences, facts and summaries into records stored under **namespaces**. The important choice is the namespace:

```
/users/{am_id}/preferences/
/accounts/{account_id}/notes/
/accounts/{account_id}/meetings/
```

For account memory, the **account** is the owner in the namespace, not the person talking. That one choice fixes the handover problem: a new account manager inherits Acme's notes, because they were never the old account manager's notes. Preferences stay personal and are deleted when the person leaves.

## Decision 2: The CRM always wins

The second finding, the champion who had left, happened because the memory stored a fact the CRM already owned.

So memory **never stores system-of-record facts**: contact roles, who has left, deal stages, amounts, contract dates. The assistant reads those live from the CRM, through a tool, every time. Memory holds only what the CRM can't: context, preferences, concerns, how decisions get made.

Two rules make this stick:

1. **At write time**, a note that is really a CRM field ("Priya is the champion") is not saved as a note. The assistant suggests updating the CRM instead.
2. **At read time**, if a note disagrees with the CRM, the CRM wins, and the assistant says so: *"Your notes say Priya Shah is the main contact, but the CRM shows she left in August. Should I remove that note?"*

This is the same rule Case 03 used for code, docs and schema: each source is the authority for one kind of question, and a good answer says which one it used.

## Decision 3: Retrieval is scoped by account and by CRM access

The first finding, the leaked discount, happened because one person's memory covered many accounts and nothing stopped them blending.

![Retrieval only ever looks inside one account, and only if the CRM says you can see it.](images/02-read-path.png)
*Retrieval only ever looks inside one account, and only if the CRM says you can see it.*

- **One account per briefing.** When preparing for Globex, the assistant retrieves from `/accounts/globex/` and nowhere else. There is no search across all accounts.
- **Access comes from the CRM.** Before retrieving anything, code checks that the person is on Globex's account team in the CRM. If they're not, nothing is retrieved, whatever they ask. That's the rule from Case 01: access is decided by data, never by the model.
- **Preferences are the only cross-account memory**, and they're about the person, not any customer.

Questions that really span accounts ("which of my accounts mentioned the competitor?") are answered from CRM reports, not from memory.

## Decision 4: Decide what may be remembered, and let people see it

The third finding, the hospital detail, was the most serious. The fix has three parts.

![Every note passes a filter before it is stored. Shared notes need a person to confirm.](images/03-write-path.png)
*Every note passes a filter before it is stored. Shared notes need a person to confirm.*

**An allow-list of note types.** Account notes may record business context: priorities, concerns, how decisions are made, risks, commitments made in meetings, communication preferences at work. Anything outside those types is not saved.

**A deny-list, checked by a second layer.** Health, family, religion, politics, personal life, and anything about a colleague's performance are never stored. The extraction instructions say so, and a separate check runs on every extracted note before it's written: Amazon Bedrock Guardrails with denied topics and sensitive-information filters. A note that trips it is dropped and logged as dropped, without its text.

**Shared notes need a confirmation.** Account notes are visible to the whole account team, so the assistant asks before saving: *"Save to Acme's notes: 'Operations lead prefers short decks, five slides or fewer'?"* Personal preferences can be saved without asking.

And people can see and change what's stored. *"What do you remember about Acme?"* lists every note with its source (who, when, which conversation) and offers edit and delete. Delete really deletes the record; it doesn't just hide it.

## Decision 5: Everything expires unless someone confirms it

Notes go stale quietly. The fix is to make staleness the default.

- **Session events:** 30 days.
- **Preferences:** one year.
- **Account notes:** 180 days, unless reconfirmed.
- **Meeting summaries:** two years.

AgentCore Memory supports a time-to-live per strategy for long-term records, so expiry is configuration, not a clean-up job someone forgets to run.

Reconfirmation is built into normal use. When the assistant uses a note older than 90 days, it marks it: *"From May, still true?"* A yes resets the clock; a no deletes it. Nobody has to schedule a review.

## The design in one picture

![Three memory scopes, one live CRM, and a filter on every write.](images/04-architecture.png)
*Three memory scopes, one live CRM, and a filter on every write.*

The assistant runs on AgentCore Runtime. Tools read the CRM, recent emails and support tickets live, and an access check runs before any of them. AgentCore Memory holds the session, preferences, account notes and meeting summaries in separate namespaces, each with its own expiry. Every write passes through the filter.

## A sketch of the briefing

```python
def briefing(am, account_id, question):
    # Access from the CRM, checked in code.
    if not crm.on_account_team(am.id, account_id):
        return refuse("not on account team")

    live = crm.snapshot(account_id)  # wins
    notes = memory.retrieve(
        namespace=f"/accounts/{account_id}/notes/",
        query=question, top_k=15)
    prefs = memory.retrieve(
        namespace=f"/users/{am.id}/preferences/",
        query=question, top_k=5)

    checked = []
    for n in notes:
        if conflicts_with(n, live):
            n.flag = "crm_disagrees"  # ask to remove
        elif n.age_days > 90:
            n.flag = "confirm"  # still true?
        checked.append(n)

    return compose(question, live, checked, prefs)
```

Notice what's missing: no line retrieves across accounts, and no line lets a note override the CRM.

## Testing memory

Memory needs its own tests in the release gate from Case 05, because the failures are about what is stored and who sees it, not about how well the answer reads.

![Memory tests, run on every release.](images/t3-tests.png)
*Memory tests, run on every release.*

The cross-account test is the one that matters most. Seed two accounts with distinctive, invented facts ("Acme: discount code ZEBRA-18"), prepare a briefing for the other account, and check the text and the retrieved records. It must be zero leaks, every release.

## What changed

With planning figures: context per session dropped from about 60,000 tokens to about 6,000 (a CRM snapshot, up to 15 notes and a few preferences). Briefings got faster and cheaper, and more relevant, because they no longer included 29 conversations about other customers.

## What can still go wrong

![What can still go wrong, and how you would catch it.](images/t4-risks.png)
*What can still go wrong, and how you would catch it.*

The numbers to watch are the **share of notes flagged as conflicting with the CRM** and the **share of notes confirmed when asked**. If conflicts rise, notes are drifting into CRM territory. If confirmations fall, notes are going stale faster than 180 days.

**At 10x**, I'd expect these to change first:

- With thousands of notes per large account, notes need structure (by stakeholder, by topic), not just a list.
- Legal will want a data-retention review of meeting summaries, and an export when a customer asks what we store about their people.
- Teams will ask for memory across accounts ("what are customers saying about the new pricing?"). That's an analytics question, and it belongs in a reporting pipeline with its own access rules, not in memory retrieval.

## What we would do differently

- **Write the deny-list with legal on day one.** It was written after the incident, which is the wrong order.
- **Put the account, not the person, in the namespace from the start.** Retrofitting meant re-extracting three months of notes.
- **Show people their memories early.** Account managers corrected dozens of wrong notes in the first week they could see them.

## Key takeaways

1. **Memory is data.** Give every memory an owner, a scope, a source and an expiry.
2. **Separate the kinds of memory.** Session, personal preferences, account notes and meeting summaries have different owners and lifetimes.
3. **The system of record wins.** Don't remember what the CRM knows; read it live, and flag notes that disagree.
4. **Scope retrieval by account and by CRM access,** checked in code before anything is retrieved.
5. **Filter every write, and confirm shared ones.** An allow-list of note types, a deny-list checked by a second layer, and a person confirming anything the team will see.
6. **Make expiry the default.** Notes expire unless someone confirms they're still true.

---

*Next in the series: Case 09, one agent or five? A research assistant (GCP). The design and decision records for this case are in the [series repository](https://github.com/prasanth2006z/ai-architecture-casebook/tree/main/cases/08-account-manager-memory).*

*How would you have handled it? I'd like to hear other approaches in the comments.*

*AWS details reflect public documentation as of October 2026. Check current docs before you build.*
