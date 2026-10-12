"""Tests for the Markdown table and the JSON results file (research R9, results-file contract).

All identifiers are synthetic.
"""

import json
import re
from pathlib import Path

from evals.models import (
    Configuration,
    EvaluationRun,
    Question,
    RetrievalResult,
    UserProfile,
)
from evals.report import render_markdown, write_results_json
from evals.runner import run_evaluation

PROFILE = UserProfile(country="DE", grade_band="L3")

HEADER = [
    "Configuration",
    "Hit@5",
    "Section hit@5",
    "MRR@5",
    "Cross-entitlement",
    "Latency p50 (ms)",
    "Latency p95 (ms)",
    "Errors",
]


def question(
    qid: str, expected_document: str | None = "a", should_refuse: bool = False
) -> Question:
    return Question(
        id=qid,
        question=f"text of {qid}",
        profile=PROFILE,
        expected_document=expected_document,
        expected_section=None,
        should_refuse=should_refuse,
        not_entitled_documents=(),
    )


def result(document_id: str) -> RetrievalResult:
    return RetrievalResult(document_id=document_id, chunk_id="c", score=0.5)


def make_run(questions: list[Question] | None = None) -> EvaluationRun:
    """q1 is a hit at rank 1, q2 is a miss: hit rate 50.0%, MRR 0.500."""

    def retrieve(text: str, profile: UserProfile) -> list[RetrievalResult]:
        return [result("a")] if text == "text of q1" else [result("x")]

    return run_evaluation(
        questions or [question("q1"), question("q2")],
        [Configuration(name="semantic", retrieve=retrieve)],
        k=5,
        question_file="questions.jsonl",
    )


def table_rows(markdown: str) -> list[list[str]]:
    rows = []
    for line in markdown.splitlines():
        if line.startswith("|") and not re.fullmatch(r"\|[\s:|-]+\|", line):
            rows.append([cell.strip() for cell in line.strip("|").split("|")])
    return rows


# --- Markdown ---------------------------------------------------------------------------


def test_table_columns_are_in_the_documented_order() -> None:
    rows = table_rows(render_markdown(make_run()))
    assert rows[0] == HEADER


def test_one_row_per_configuration_with_formatted_values() -> None:
    rows = table_rows(render_markdown(make_run()))
    assert len(rows) == 2
    row = dict(zip(HEADER, rows[1], strict=True))
    assert row["Configuration"] == "semantic"
    assert row["Hit@5"] == "50.0%"
    assert row["MRR@5"] == "0.500"
    assert row["Cross-entitlement"] == "0"
    assert row["Errors"] == "0"
    assert re.fullmatch(r"\d+\.\d", row["Latency p50 (ms)"])
    assert re.fullmatch(r"\d+\.\d", row["Latency p95 (ms)"])


def test_na_is_shown_where_a_metric_is_undefined() -> None:
    row = dict(zip(HEADER, table_rows(render_markdown(make_run()))[1], strict=True))
    assert row["Section hit@5"] == "n/a"  # no question has an expected section


def test_every_na_cell_gets_a_notes_line() -> None:
    markdown = render_markdown(make_run())
    notes = [line for line in markdown.splitlines() if line.startswith("- ")]
    assert any("Section hit@5" in line and "semantic" in line and "n/a" in line for line in notes)


def test_all_refusal_questions_make_hit_rate_and_mrr_na() -> None:
    questions = [question("q1", expected_document=None, should_refuse=True)]
    markdown = render_markdown(make_run(questions))
    row = dict(zip(HEADER, table_rows(markdown)[1], strict=True))
    assert row["Hit@5"] == "n/a"
    assert row["MRR@5"] == "n/a"
    notes = [line for line in markdown.splitlines() if line.startswith("- ")]
    assert any("Hit@5" in line for line in notes)
    assert any("MRR@5" in line for line in notes)


def test_footer_states_k_question_count_and_file_name() -> None:
    markdown = render_markdown(make_run())
    assert "k = 5" in markdown
    assert "2 questions" in markdown
    assert "questions.jsonl" in markdown


# --- JSON -------------------------------------------------------------------------------


def read_json(tmp_path: Path, run: EvaluationRun) -> tuple[str, dict[str, object]]:
    path = tmp_path / "results.json"
    write_results_json(run, path)
    text = path.read_text(encoding="utf-8")
    return text, json.loads(text)


def test_json_uses_sorted_keys_and_two_space_indentation(tmp_path: Path) -> None:
    text, data = read_json(tmp_path, make_run())
    assert text == json.dumps(data, indent=2, sort_keys=True) + "\n"


def test_json_top_level_shape(tmp_path: Path) -> None:
    _, data = read_json(tmp_path, make_run())
    assert set(data) == {"k", "question_file", "question_count", "configurations"}
    assert data["k"] == 5
    assert data["question_file"] == "questions.jsonl"
    assert data["question_count"] == 2


def test_json_has_no_timestamps_or_run_ids(tmp_path: Path) -> None:
    text, _ = read_json(tmp_path, make_run())
    assert not re.search(r'"[^"]*(timestamp|time_stamp|run_id|created|date)[^"]*":', text)


def test_json_summary_and_outcomes_match_the_contract(tmp_path: Path) -> None:
    _, data = read_json(tmp_path, make_run())
    (cfg,) = data["configurations"]  # type: ignore[misc]
    assert set(cfg) == {"name", "summary", "outcomes"}
    assert cfg["name"] == "semantic"
    assert set(cfg["summary"]) == {
        "hit_rate",
        "section_hit_rate",
        "mrr",
        "cross_entitlement_total",
        "latency_p50_ms",
        "latency_p95_ms",
        "error_count",
        "correct_refusal_rate",
        "false_refusal_rate",
        "citation_validity",
    }
    assert cfg["summary"]["hit_rate"] == {"value": 0.5, "numerator": 1, "denominator": 2}
    assert cfg["summary"]["section_hit_rate"] == {"value": None, "numerator": 0, "denominator": 0}
    assert cfg["summary"]["error_count"] == 0

    first = cfg["outcomes"][0]
    assert set(first) == {
        "question_id",
        "results",
        "document_hit",
        "section_hit",
        "reciprocal_rank",
        "cross_entitlement_count",
        "latency_ms",
        "refused",
        "refusal_correct",
        "false_refusal",
        "citations_valid",
        "error",
    }
    assert first["question_id"] == "q1"
    assert first["results"] == [
        {"document_id": "a", "chunk_id": "c", "score": 0.5, "section": None}
    ]
    assert first["error"] is None
    assert first["refused"] is None


def strip_latency(data: dict[str, object]) -> dict[str, object]:
    for cfg in data["configurations"]:  # type: ignore[attr-defined]
        cfg["summary"].pop("latency_p50_ms")
        cfg["summary"].pop("latency_p95_ms")
        for outcome in cfg["outcomes"]:
            outcome.pop("latency_ms")
    return data


def test_two_runs_give_identical_json_except_latency(tmp_path: Path) -> None:
    _, first = read_json(tmp_path, make_run())
    _, second = read_json(tmp_path, make_run())
    assert strip_latency(first) == strip_latency(second)
