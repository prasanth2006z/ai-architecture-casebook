# Contract: Python plug-in API

Public names exported from `evals`:

```python
Configuration(name: str, retrieve: RetrieveFn, answer: AnswerFn | None = None)
run_evaluation(questions: list[Question], configurations: list[Configuration], k: int = 5, question_file: str = "") -> EvaluationRun
load_questions(path: Path) -> list[Question]          # raises QuestionFileError
render_markdown(run: EvaluationRun) -> str
write_results_json(run: EvaluationRun, path: Path) -> None
```

Callable shapes (plain functions or lambdas, no base class):

```python
RetrieveFn = Callable[[str, UserProfile], list[RetrievalResult]]
AnswerFn   = Callable[[str, UserProfile, list[RetrievalResult]], Answer]
```

## Behavior guarantees

- `retrieve` is called exactly once per question per configuration, in question-file order.
- `answer` is called once per question, only if supplied, and receives the same results that `retrieve` returned.
- An exception from either callable is recorded on that question's outcome (stage `retrieve` or `answer`) and never propagates. The question then scores as a miss for hit rate, section hit rate and MRR.
- `run_evaluation` raises `ValueError` for `k < 1`, an empty question list, an empty configuration list, or duplicate configuration names.
- Results from `retrieve` must be ordered best first; the harness does not re-sort them.
- Every result must carry a non-empty text `document_id`. A result that does not is treated as a cross-entitlement retrieval (fail closed) and its question is recorded as an error with stage `validate`. Every errored question, whatever the stage, scores as a miss for hit rate, section hit rate and MRR; the cross-entitlement count still includes the unverifiable results. The `answer` callable is not called for a `validate` error.
