"""End-to-end run of the committed 3-question sample (SC-001, SC-002, FR-017)."""

import importlib.util
import json
from pathlib import Path

from evals import load_questions, render_markdown, run_evaluation, write_results_json
from evals.models import Configuration

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


def load_sample_configs() -> dict[str, Configuration]:
    spec = importlib.util.spec_from_file_location("sample_configs", SAMPLES / "sample_configs.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return {"semantic": module.semantic, "hybrid": module.hybrid}


def test_sample_set_has_three_synthetic_questions() -> None:
    questions = load_questions(SAMPLES / "questions.jsonl")
    assert [q.id for q in questions] == ["q1", "q2", "q3"]
    assert sum(q.should_refuse for q in questions) == 1


def test_sample_runs_end_to_end_and_produces_table_and_results_file(tmp_path: Path) -> None:
    questions = load_questions(SAMPLES / "questions.jsonl")
    configs = load_sample_configs()

    run = run_evaluation(
        questions, [configs["semantic"], configs["hybrid"]], k=5, question_file="questions.jsonl"
    )
    markdown = render_markdown(run)
    write_results_json(run, tmp_path / "results.json")

    assert "| semantic" in markdown
    assert "| hybrid" in markdown
    data = json.loads((tmp_path / "results.json").read_text(encoding="utf-8"))
    assert [c["name"] for c in data["configurations"]] == ["semantic", "hybrid"]
    assert all(len(c["outcomes"]) == 3 for c in data["configurations"])


def test_sample_semantic_configuration_deliberately_returns_one_forbidden_document() -> None:
    # The sample shows a non-zero cross-entitlement count (documented in samples/README.md).
    questions = load_questions(SAMPLES / "questions.jsonl")
    configs = load_sample_configs()

    run = run_evaluation(questions, [configs["semantic"], configs["hybrid"]])

    totals = {c.summary.name: c.summary.cross_entitlement_total for c in run.configurations}
    assert totals == {"semantic": 1, "hybrid": 0}
