# code-index

Chunks the ClaimFlow Node.js backend by function, class and HTTP route for the team knowledge assistant. Design: [ADR-007](../../adr/ADR-007-code-chunks-and-module-summaries.md).

```
npm install
npm test

# first load / nightly reconcile: every file at the deployed commit
node index-repo.js full /path/to/claimflow prod > chunks.jsonl

# on each deploy: only what changed between the previous and new prod commit
node index-repo.js diff /path/to/claimflow <oldProdSha> <newProdSha> > changes.jsonl
```

Output is JSON lines:

| `op` | Meaning | Loader action |
|---|---|---|
| `file` | All chunks for one file | Compare with stored `{key: hash}` using `planFileUpdate`; embed and upsert changed chunks; delete missing keys |
| `delete_file` | File removed or renamed away | Delete every chunk with this path |
| `modules` | Modules touched | For each, recompute `moduleInputHash`; if changed, build `moduleDigest`, call the model with `SUMMARY_PROMPT`, store the summary |

## Rolling it out on the running system

1. **Mark what's in production.** Add one step to the deploy pipeline: `git tag -f prod <deployed-sha> && git push -f origin prod`. The indexer always reads that tag.
2. **Create the store.** Tables for chunks (key, path, module, kind, symbol, text, hash, commit, calls, tables, embedding), module summaries (module, input_hash, summary, commit, model, prompt_version) and sync state (last indexed prod SHA).
3. **First load.** Run `full` on `prod`, embed every chunk, then generate every module summary. Record the prod SHA as `last_indexed`.
4. **Wire the trigger.** Bitbucket webhook on `repo:push` → Cloud Run endpoint → verify `X-Hub-Signature` → if the `prod` tag moved, run `diff <last_indexed> <new prod>` and apply it. Update `last_indexed` only after the apply succeeds.
5. **Nightly reconcile.** Run `full` on `prod`; hashes make unchanged files free. This catches missed webhooks.
6. **Compare before switching.** Keep the current ChatGPT context in use. Run the golden questions (ADR-006) against both, and switch when the index wins. Move anything that exists only in the old context into Confluence.

## Adapting to your codebase

- **Includes and excludes** are at the top of `index-repo.js`.
- **Routes:** any `x.get/post/put/patch/delete('/path', ...)` call. If routes are registered another way (a route table, decorators), add a rule in `routeOf`.
- **Tables:** knex-style calls, `tableName`, `@Entity`, Prisma models and SQL strings are detected. Add your data-access helper to `TABLE_CALLS` if it takes the table name as its first argument.
- **Thresholds:** `TINY_LINES` and `MAX_LINES` in `chunker.js`.
