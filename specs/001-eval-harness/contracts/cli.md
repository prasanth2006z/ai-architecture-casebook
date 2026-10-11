# Contract: command line

```text
evals run --questions FILE --config SPEC [--config SPEC ...] [--k N] [--out-dir DIR]
```

| Argument | Meaning |
|----------|---------|
| `--questions FILE` | JSONL question file (required) |
| `--config SPEC` | `module:attr` or `path/to/file.py:attr`; repeatable; at least one. `attr` is a `Configuration` or a zero-argument function returning one |
| `--k N` | cutoff for hit rates, default 5 |
| `--out-dir DIR` | directory for `results.md` and `results.json`; default `./eval-results` |

## Behavior

- Prints the Markdown table to stdout and writes `results.md` and `results.json` to the output directory (created if missing).
- Exit code 0 when the run completes, even if some questions errored (the error count is in the table).
- Exit code 2 for usage errors, an unreadable or malformed question file, or a configuration that cannot be loaded. The message goes to stderr and names the cause. No traceback.
- Makes no network calls.

## Example

```text
uv run evals run --questions samples/questions.jsonl \
  --config samples/sample_configs.py:semantic \
  --config samples/sample_configs.py:hybrid
```
