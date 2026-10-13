# Data Model: Synthetic HR Policy Dataset

## Entities

### Policy (a generated document)

| Field | Meaning | Rules |
|-------|---------|-------|
| `document_id` | Stable id, also the file stem | Lower-case; `<topic>-<country>`, `<topic>-global`, or `<topic>-<country>-v1` for superseded |
| `topic` | Template key | One of the topics below |
| `title` | Human title | Includes country name for country documents |
| `policy_code` | Code in the body, e.g. `HR-LV-UK-003` | Differs per country; unique |
| `sections` | Numbered sections `1`, `2`, `3.1`, `3.2`, ... | Every document has at least 4 sections; section ids are unique within a document |
| `body` | Rendered Markdown | Starts with the synthetic label line |

### Metadata (sidecar, `<document_id>.md.metadata.json`)

| Field | Type | Rules |
|-------|------|-------|
| `document_id` | text | Equals file stem |
| `title` | text | Non-empty |
| `allowed_countries` | list of text | Subset of `UK`, `IN`; non-empty; both for global documents |
| `allowed_grades` | list of text | Subset of `G1-6`, `G7+`; non-empty; `["G7+"]` for restricted |
| `version` | text | `1.0` or `2.0` style |
| `effective_date` | ISO date text | Superseded version's date is earlier than its current version's |
| `status` | text | `current` or `superseded` |
| `synthetic` | boolean | Always `true` |

Written as `{"metadataAttributes": { ...above... }}` (see [research.md](research.md) R3).

### Question (one JSONL line)

Exactly the harness contract keys: `id`, `question`, `profile` (`country`, `grade_band`), `expected_document`, `expected_section`, `should_refuse`, `not_entitled_documents`. See [contracts/dataset-files.md](contracts/dataset-files.md).

### Asker profile

`country` in {`UK`, `IN`}, `grade_band` in {`G1-6`, `G7+`}. Entitled to a document exactly when `country` is in `allowed_countries` and `grade_band` is in `allowed_grades`.

## Corpus plan (target 51 documents)

| Group | Topics | Documents |
|-------|--------|-----------|
| Leave | annual-leave, sick-leave, public-holidays, special-leave | 4 topics x 2 countries = 8 |
| Parental leave | parental-leave, adoption-leave, carers-leave | 3 x 2 = 6 |
| Travel | business-travel, travel-booking, relocation-standard | 3 x 2 = 6 |
| Expenses | expense-claims, meal-allowance, mobile-reimbursement | 3 x 2 = 6 |
| Remote work | remote-work, home-office-equipment | 2 x 2 = 4 |
| Benefits | health-insurance, retirement-savings, learning-budget | 3 x 2 = 6 |
| **Country topics** | 18 topics | **36** |
| Restricted (G7+ only) | exec-relocation, exec-compensation, exec-travel, exec-health-screening | 4 x 2 = 8 |
| Superseded versions | business-travel-uk-v1, expense-claims-in-v1, parental-leave-uk-v1, remote-work-in-v1 | 4 |
| Global | code-of-conduct, anti-harassment, data-privacy-for-hr | 3 |
| **Total** | | **51** |

The superseded set shares sections with its current version but differs in at least one number. The injection probe is `remote-work-uk` section 5.

## Value table (`data/values.toml`)

Keyed by topic, then country, then grade band (a `default` entry applies to both bands). Value names are template placeholders: `$country_name`, `$policy_code`, `$days`, `$weeks`, `$notice_days`, `$limit`, `$currency`, `$authority`, `$effective_date`, `$min_service_months`, and similar. A missing value fails the build.

## Question table (`data/questions.toml`)

Per question: `id`, `question`, `country`, `grade_band`, `topic` (resolved to the asker's country document) or `expected_document`, `expected_section`, `refuse` (bool). No entitlement list in the table.

| Id prefix | Count | Rule |
|-----------|-------|------|
| `s01-s30` | 30 | One country; expected document is current and entitled; at least 6 target a superseded family and 8 target a split rule/condition |
| `c01-c15` | 15 | Topic exists in both countries; expected document is the asker's own country |
| `o01-o10` | 10 | Out of scope; `should_refuse` true; expected document and section null |
| `p01-p05` | 5 | `p01-p03` fallback to an entitled current document; `p04-p05` refusals; the restricted document is in the not-entitled list |

## Relationships and invariants

- Every sidecar has exactly one Markdown file and vice versa.
- Per policy family (`topic` + country) exactly one document has `status: current`.
- Not-entitled list of any question = all documents whose country list excludes the asker's country, plus all remaining documents whose grade list excludes the asker's grade. Global documents covering the asker's country never appear. Superseded documents follow the same rule (they are not special-cased).
- Expected document of a non-refusal question: entitled, `status: current`, contains the expected section id.
- The superseded documents may appear in a not-entitled list only because of country or grade; being superseded is handled by the status filter, not by entitlement (POCs 2 and 3 test them separately).

## State transitions

None. A policy family goes `current` / `superseded` only at build time from the catalog.
