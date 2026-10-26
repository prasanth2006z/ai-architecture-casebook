# Publish checklist: Case 04

**Title:** An LLM Gateway That Cut the Bill: Meter First, Then Route

**Subtitle:** A design case study: why a growing model bill is usually a routing and caching problem, and how one small gateway made it visible and then smaller.

**Cloud:** Google Cloud · **Words:** ~2,448 · **Images:** 11

**Tags (Medium allows 5):** LLM, Google Cloud, FinOps, AI Architecture, Generative AI

**Repository folder:** `cases/04-llm-gateway/` (design.md, adr/, images/)

## Before scheduling

- [ ] Paste the title and subtitle into Medium's title/subtitle fields (remove them from the body).
- [ ] Upload each image at its marker, in the order below. Use the caption line under each image as the Medium caption, and the alt text as the image's alt text.
- [ ] Paste code blocks as Medium code blocks (Ctrl/Cmd + Alt + 6). They are already narrow enough for mobile.
- [ ] Set the cover image (`images/00-cover.png`) as the story's featured image.
- [ ] Add the 5 tags.
- [ ] Check the footer link points to the repository folder and push `design.md`, `adr/` and `images/` to that folder before publishing.
- [ ] Re-check any service details flagged "as of October 2026" if publishing much later.
- [ ] Add the story to the "AI Architecture Casebook" list / publication.

## Images in order

| # | File | Alt text / caption |
|---|---|---|
| 1 | `images/00-cover.png` | Cover |
| 2 | `images/01-the-bill.png` | The bill quadrupled in nine months, and nobody could say which app caused it. |
| 3 | `images/t1-requirements.png` | The first two rows cannot bend. |
| 4 | `images/02-architecture.png` | Every model call goes through one gateway, which meters, limits, routes and caches. |
| 5 | `images/t2-gateway-options.png` | Four ways to put a door in front of the models. |
| 6 | `images/03-where-the-money-went.png` | Where the September bill went, by cause. |
| 7 | `images/04-route-by-use-case.png` | Each use case has a tier. Moving it to a cheaper one needs a passing evaluation. |
| 8 | `images/05-cache-layers.png` | Three layers of caching, from safest to riskiest. |
| 9 | `images/t3-budget-behaviour.png` | What happens at the budget depends on who is calling. |
| 10 | `images/06-savings.png` | From about $48,000 to about $20,000 a month. Most of it came from routing, not discounts. |
| 11 | `images/t4-risks.png` | What can still go wrong, and how you would catch it. |

`post-preview.html` shows the post with images in place, for a final read before pasting into Medium.
