# ADR-004: Citations are verified by code against stored pages; failures are shown, not hidden

- **Status:** Proposed
- **Date:** 2026-10-26
- **Case:** 09 · One agent or five? A research assistant (Google Cloud)
- **Related:** ADR-003

## Context

Even with notes, a writer can attach the wrong note to a sentence. Whether a citation is correct is an exact question.

## Decision

1. Every fetched page's text is stored in Cloud Storage at fetch time.
2. For each sentence: every cited note exists and its source was fetched in this run; the note's quote appears verbatim (after whitespace/punctuation normalisation) in the stored page; the note's date is within the question's range.
3. Sentences that fail move to an "Unverified" section shown to the analyst.
4. Judging whether a claim is well supported stays with the analyst.

## Consequences

- Some correct sentences are marked unverified when pages are reformatted; normalisation rules are tuned.
- Stored pages enable later audit.

## Verification

- Citation errors reaching the analyst = 0 on the task set.
- "Unverified" share tracked per week.
