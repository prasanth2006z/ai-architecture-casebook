"""Run-level entitlement tests (spec User Story 2, FR-007, FR-014a, SC-003).

The unit tests for the check itself are in test_entitlement.py. These tests prove the count
reaches the outcomes, the table and the results file, including the fail-closed case.
All identifiers are synthetic.
"""

import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

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


def question(
    qid: str = "q1",
    expected_document: str | None = "a",
    expected_section: str | None = None,
    should_refuse: bool = False,
    not_entitled: tuple[str, ...] = ("secret",),
) -> Question:
    return Question(
        id=qid,
        question=f"text of {qid}",
        profile=PROFILE,
        expected_document=expected_document,
        expected_section=expected_section,
        should_refuse=should_refuse,
        not_entitled_documents=not_entitled,
    )


def result(document_id: str, section: str | None = None) -> RetrievalResult:
    return RetrievalResult(document_id=document_id, chunk_id="c", score=0.5, section=section)


def unverifiable(kind: str) -> object:
    """A returned result whose document id cannot be verified."""
    if kind == "empty":
        return RetrievalResult(document_id="", chunk_id="c-bad", score=0.5)
    if kind == "none":
        return SimpleNamespace(document_id=None, chunk_id="c-bad", score=0.5, section=None)
    if kind == "non_text":
        return SimpleNamespace(document_id=42, chunk_id="c-bad", score=0.5, section=None)
    return SimpleNamespace(chunk_id="c-bad")  # "missing": no document_id, score or section


UNVERIFIABLE_KINDS = ["empty", "none", "non_text", "missing"]


def run_with(questions: list[Question], returned: list[object]) -> EvaluationRun:
    config = Configuration(name="c", retrieve=lambda text, profile: list(returned))  # type: ignore[arg-type, return-value]
    return run_evaluation(questions, [config], k=5, question_file="qs.jsonl")


def cell(markdown: str, column: str) -> str:
    rows = [
        [c.strip() for c in line.strip("|").split("|")]
        for line in markdown.splitlines()
        if line.startswith("|")
    ]
    return rows[2][rows[0].index(column)]


# --- counting forbidden results ----------------------------------------------------------


def test_each_forbidden_result_adds_one_to_the_outcome_and_the_total() -> None:
    run = run_with([question()], [result("a"), result("secret"), result("secret")])

    (outcome,) = run.configurations[0].outcomes
    assert outcome.cross_entitlement_count == 2
    assert run.configurations[0].summary.cross_entitlement_total == 2
    assert cell(render_markdown(run), "Cross-entitlement") == "2"


def test_forbidden_document_that_is_also_the_expected_one_is_still_counted() -> None:
    run = run_with([question(expected_document="secret")], [result("secret")])

    (outcome,) = run.configurations[0].outcomes
    assert outcome.cross_entitlement_count == 1
    assert outcome.document_hit is True  # a hit on quality, and still a cross-entitlement count
    assert cell(render_markdown(run), "Cross-entitlement") == "1"


def test_no_forbidden_results_shows_zero_in_the_table() -> None:
    run = run_with([question()], [result("a")])
    assert run.configurations[0].summary.cross_entitlement_total == 0
    assert cell(render_markdown(run), "Cross-entitlement") == "0"


def test_the_total_adds_up_across_questions() -> None:
    questions = [question("q1"), question("q2")]
    run = run_with(questions, [result("secret")])
    assert run.configurations[0].summary.cross_entitlement_total == 2


# --- fail closed: unverifiable document ids ---------------------------------------------


@pytest.mark.parametrize("kind", UNVERIFIABLE_KINDS)
def test_unverifiable_result_is_counted_and_the_question_is_an_error(kind: str) -> None:
    run = run_with([question(expected_section="s1")], [unverifiable(kind)])

    (outcome,) = run.configurations[0].outcomes
    assert outcome.cross_entitlement_count == 1
    assert outcome.error is not None
    assert outcome.error.stage == "validate"
    assert "document id" in outcome.error.message
    assert run.configurations[0].summary.cross_entitlement_total == 1
    assert run.configurations[0].summary.error_count == 1


@pytest.mark.parametrize("kind", UNVERIFIABLE_KINDS)
def test_unverifiable_result_scores_as_a_miss_for_every_quality_metric(kind: str) -> None:
    run = run_with([question(expected_section="s1")], [unverifiable(kind)])

    (outcome,) = run.configurations[0].outcomes
    assert outcome.document_hit is False
    assert outcome.section_hit is False
    assert outcome.reciprocal_rank == 0.0
    assert outcome.latency_ms is None


@pytest.mark.parametrize("kind", UNVERIFIABLE_KINDS)
def test_errored_question_stays_in_every_denominator(kind: str) -> None:
    questions = [question("q1", expected_section="s1"), question("q2", expected_section="s1")]

    def retrieve(text: str, profile: UserProfile) -> list[object]:
        if text == "text of q1":
            return [result("a", "s1")]  # a clean hit
        return [unverifiable(kind)]

    config = Configuration(name="c", retrieve=retrieve)  # type: ignore[arg-type]
    summary = run_evaluation(questions, [config]).configurations[0].summary

    assert (summary.hit_rate.numerator, summary.hit_rate.denominator) == (1, 2)
    assert (summary.mrr.numerator, summary.mrr.denominator) == (1.0, 2)
    assert summary.section_hit_rate.denominator == 2
    assert summary.error_count == 1


def test_latency_of_an_errored_question_is_excluded_from_the_percentiles() -> None:
    run = run_with([question()], [unverifiable("empty")])
    summary = run.configurations[0].summary
    assert summary.latency_p50_ms is None
    assert summary.latency_p95_ms is None


def test_the_error_overrides_a_hit_when_the_expected_document_is_also_returned() -> None:
    run = run_with([question()], [result("a"), unverifiable("empty")])

    (outcome,) = run.configurations[0].outcomes
    assert outcome.document_hit is False
    assert outcome.reciprocal_rank == 0.0
    assert outcome.error is not None


def test_other_results_are_still_checked_alongside_an_unverifiable_one() -> None:
    run = run_with([question()], [unverifiable("none"), result("secret"), result("a")])

    (outcome,) = run.configurations[0].outcomes
    assert outcome.cross_entitlement_count == 2  # the unverifiable one and the forbidden one


def test_unverifiable_result_counts_even_with_an_empty_forbidden_list() -> None:
    run = run_with([question(not_entitled=())], [unverifiable("empty")])
    (outcome,) = run.configurations[0].outcomes
    assert outcome.cross_entitlement_count == 1
    assert outcome.error is not None


def test_refusal_question_without_an_expected_document_is_still_an_error() -> None:
    refusal = question(expected_document=None, should_refuse=True)
    run = run_with([refusal], [unverifiable("empty")])

    (outcome,) = run.configurations[0].outcomes
    assert outcome.error is not None
    assert outcome.cross_entitlement_count == 1
    assert outcome.document_hit is None  # excluded from the rate, as for any refusal question
    assert outcome.reciprocal_rank is None
    assert run.configurations[0].summary.hit_rate.denominator == 0


def test_the_table_shows_the_leak_and_the_error() -> None:
    run = run_with([question()], [unverifiable("empty")])
    markdown = render_markdown(run)
    assert cell(markdown, "Cross-entitlement") == "1"
    assert cell(markdown, "Errors") == "1"
    assert cell(markdown, "Hit@5") == "0.0%"


@pytest.mark.parametrize("kind", UNVERIFIABLE_KINDS)
def test_the_results_file_records_the_error_without_crashing(kind: str, tmp_path: Path) -> None:
    run = run_with([question()], [unverifiable(kind)])
    path = tmp_path / "results.json"
    write_results_json(run, path)

    outcome = json.loads(path.read_text(encoding="utf-8"))["configurations"][0]["outcomes"][0]
    assert outcome["cross_entitlement_count"] == 1
    assert outcome["error"]["stage"] == "validate"
    assert re.search(r"document id", outcome["error"]["message"])
    assert outcome["latency_ms"] is None
    assert len(outcome["results"]) == 1
