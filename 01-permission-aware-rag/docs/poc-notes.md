# Case Study 01: POC notes

Working notes for the POCs. These are not decisions: a note that changes what a POC must do moves into the relevant ADR when the POC proves it.

## POC 1 (chunking): chunks need document context

Status: note, 2026-10-12. Related: [ADR-003](adr/ADR-003-section-based-chunking.md).

The UK and India versions of a policy are near-identical, and a section on its own contains no country words. For example, section 3.1 of the parental leave policy reads "An eligible employee may take up to 26 weeks of parental leave per child." The words "United Kingdom" appear only in the title and the opening section. A chunk made from section 3.1 alone therefore cannot be told apart from the India version by keyword search, which is exactly what the hybrid design relies on (ADR-001).

**Requirement for the POC 1 chunker:** every chunk text is prefixed with the document title, the country and the policy code (for example `Parental Leave Policy (United Kingdom) | HR-PL-UK-001`), in addition to the section number and the metadata ADR-003 already lists. The POC should compare results with and without the prefix so the effect is measured.

Why it matters for the dataset ([spec](../../specs/002-hr-policy-dataset/spec.md)): the country-differs questions `c09`-`c15` do not name a country, so only the profile and the metadata can pick the right version; `c01`-`c08` name it, so they show what a prefixed chunk gains from keyword matching.

## POC 2 (retrieval): report the two country-differs groups

Report `c01`-`c08` (country named in the question) and `c09`-`c15` (not named) separately as well as together. The id range is the group; the question file has no extra field for it.
