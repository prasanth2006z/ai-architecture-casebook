# ADR-007: Chunk code by function, class and route; rebuild module summaries only when their input changes

- **Status:** Accepted
- **Date:** 2026-10-18
- **Case:** 03 · Keeping a team knowledge assistant in sync (GCP)
- **Related:** ADR-002 (sync), ADR-003 (one representation per source)

## Context

ClaimFlow is a **Node.js** backend (JavaScript, possibly some TypeScript) running in production. Today the assistant's knowledge of the code comes from a one-off ChatGPT summary of the repository.

ADR-003 says code is chunked by function and class, with a short summary per module that is "derived and versioned". This ADR defines how, for Node.js.

Requirements:

- A chunk should be a unit someone asks about ("where is partial approval applied?", "what does `POST /claims/:id/approve-partial` do?").
- The index must describe the code **running in production**, not the latest merge.
- A deploy that touches two functions should re-embed two chunks, not the whole repository.
- Summaries must never drift from the code, and nobody edits them by hand.

## Decision

### 1. Which code: the deployed commit

The deploy pipeline moves a git tag `prod` to the commit it deploys. A Bitbucket `repo:push` webhook fires when the tag moves (ADR-002). The indexer reads files directly from that ref with `git show <ref>:<path>`, so it never needs a checkout. Optionally `main` is indexed as a second set labelled "not yet released".

### 2. Find what changed

`git diff --name-status -M <oldProd> <newProd>` lists added, modified, renamed and deleted files. Only `.js .cjs .mjs .jsx .ts .tsx` under the source tree are indexed. `node_modules`, `dist`, `build`, `coverage`, `*.min.js` and `*.d.ts` are excluded; tests are excluded by default (`--with-tests` to include). A deleted file drops all its chunks. A renamed file is deleted under the old path and indexed under the new one.

### 3. Parse and chunk

Files are parsed with the **TypeScript compiler API**. It reads JavaScript and TypeScript without type-checking and is one pure-JS dependency, so it installs anywhere Node runs.

| Code shape | Chunk |
|---|---|
| `function x()`, `const x = async () => {}`, `exports.x = function`, members of `module.exports = {...}` | One `function` chunk, with its JSDoc |
| Express-style `router.post('/claims/:id/approve-partial', auth, handler)` | One `route` chunk keyed by `POST /claims/:id/approve-partial`; handler names recorded as calls |
| Class (JS or TS) | One `class` outline: JSDoc, fields, tiny methods, method signatures; each larger method gets its own `function` chunk |
| Tiny function (≤ 4 lines) | Folded into the file or class outline |
| Function over 150 lines | Split at top-level statements; each part repeats the signature (`#part1`, `#part2`) |
| Everything else in the file | One `file` outline: imports, requires, constants, tiny functions, list of exports |

Every chunk has:

- a **key**, stable across commits: `path#symbol(params)`, `path#ROUTE VERB /path`, `path#Class`, `path#<file>`,
- a **hash** of the **code only**, never the header or commit SHA, so unchanged code keeps its hash,
- a **header** for retrieval: path, owner, symbol, commit,
- **calls**: called functions, e.g. `approval.approvePartial`, `pool.query`,
- **tables**: from knex/query builders (`db('claims')`, `.from('claims')`), raw SQL strings that start like SQL, Sequelize `tableName`, TypeORM `@Entity('claims')`, and Prisma models (`prisma.claim.update`),
- **imports**: relative `require`/`import` paths, used to show which modules depend on each other.

### 4. Update the index from hashes

For each changed file, compare stored `{key: hash}` with the new chunks:

- key new or hash different → upsert and re-embed,
- same key and hash → skip,
- key gone → delete.

A new commit with the same code, a comment between functions or a reformatted import changes nothing.

### 5. Module summaries keyed by input hash

- **Module** = directory, e.g. `src/services`.
- **Input hash** = hash of the module's sorted `key:hash` pairs.
- After each sync, recompute the input hash for every touched module. **Only if it changed**, regenerate the summary.
- The prompt gets a **digest**, not code bodies: files, exports, imports, routes with their handlers, exported function signatures, JSDoc, calls and tables. The answer has a fixed shape: Purpose · HTTP routes · Main exported functions · Tables read/written · Statuses set · Modules it depends on · Notes, and says "not visible" where the digest doesn't show something.
- Stored with: input hash, commit SHA, model name, prompt version, `generated = true`. Answers cite it as a generated summary.
- **Never edited by hand.** If a summary is wrong, fix the JSDoc or the prompt; the next deploy regenerates it. A prompt-version change regenerates all summaries in the nightly reconcile.

### 6. First load and the existing ChatGPT context

- **First load:** run the indexer in `full` mode on the current `prod` ref, then switch to `diff` mode on each tag move. The nightly reconcile also runs `full`; hashes make it cheap.
- **The existing ChatGPT context** stays in use until the new index wins on the golden set (ADR-006). Anything it contains that is not in code, Confluence or the schema (tribal knowledge, glossary terms) is moved to a Confluence page so it gets indexed and kept current.

Reference implementation: [`src/code-index/`](../src/code-index/) (`chunker.js`, `index-repo.js`, tests).

## Options considered

| Option | Why not chosen |
|---|---|
| Fixed-size line chunks | Cuts functions in half; chunks don't match questions |
| Whole files | Too coarse; any edit re-embeds the file; large files dilute the embedding |
| Babel parser | Equally good for JS/TS; TypeScript API chosen as a single dependency that also covers TS types and decorators |
| tree-sitter | Multi-language, but native bindings to build in the container; not needed for a Node-only codebase |
| Index `main` only | Answers would describe unreleased code during troubleshooting |
| Regenerate all summaries nightly | Cost and churn; wording changes without code changes |

## Consequences

- Typical deploy: a few dozen chunks re-embedded, one or two summaries regenerated.
- Route chunks let the assistant answer "what does this endpoint do?" and link the endpoint to its handler.
- Table links make "which code writes to `claim_items`?" a lookup.
- Calls are recorded by name, not resolved by type; good for navigation, not for refactoring.
- Size thresholds (4 and 150 lines) need tuning on the golden set.
- Patterns the chunker doesn't recognise (e.g. a custom route registry) fall back to the file outline until a rule is added.

## Verification

Unit tests in `src/code-index/test/chunker.test.js`:

- Express routes become route chunks linked to their handlers,
- functions and arrow functions get their own chunks; tiny ones fold into the file outline,
- JSDoc, calls and tables (knex, raw SQL) are captured; TypeScript classes get an outline plus method chunks,
- tables from Prisma, TypeORM and SQL are captured, but plain English strings are not,
- same code under a new commit → nothing to do; one function changed → only that chunk,
- function deleted → chunk deleted and file outline updated,
- comment between functions → module input hash unchanged,
- long function split into parts with the signature repeated,
- module digest contains routes, signatures, calls and tables but no bodies,
- `index-repo diff` on a real git repo handles modified, renamed and deleted files.

The chunker was also run on two open-source Express backends (one JavaScript, one TypeScript with Prisma) without errors.
