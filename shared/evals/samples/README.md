# Samples

**All sample data in this folder is synthetic.** The questions, document names, policy
sections, scores and results are invented for demonstration. They contain no real company,
customer, or personal data.

## Files

- `questions.jsonl`: three synthetic questions (two answerable, one that should be refused).
- `sample_configs.py`: two stand-in configurations, `semantic` and `hybrid`. They return
  hard-coded results, so a run is deterministic apart from latency.

## What the sample shows

- `semantic` finds the expected document for `q2` only at rank 2, and deliberately returns
  one not-entitled document (`exec-comp-policy` for `q2`), so the cross-entitlement column is
  non-zero.
- `hybrid` finds each expected document at rank 1, returns nothing for the refusal question,
  and returns no not-entitled documents.

Run it from `shared/evals/`:

```text
uv run evals run --questions samples/questions.jsonl \
  --config samples/sample_configs.py:semantic \
  --config samples/sample_configs.py:hybrid
```
