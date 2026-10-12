"""Tests for run_evaluation (spec FR-003, FR-008, FR-015, User Story 1).

All identifiers are synthetic.
"""

from dataclasses import replace

import pytest

from evals.models import (
    Configuration,
    EvaluationRun,
    Question,
    RetrievalResult,
    UserProfile,
)
from evals.runner import run_evaluation

PROFILE = UserProfile(country="DE", grade_band="L3")


def question(
    qid: str,
    expected_document: str | None = "a",
    expected_section: str | None = None,
    should_refuse: bool = False,
    not_entitled: tuple[str, ...] = (),
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


def config(name: str, results: list[RetrievalResult]) -> Configuration:
    return Configuration(name=name, retrieve=lambda text, profile: list(results))


def normalized(run: EvaluationRun) -> list[object]:
    """Everything except latency, for determinism checks."""
    parts: list[object] = []
    for cfg in run.configurations:
        summary = replace(cfg.summary, latency_p50_ms=None, latency_p95_ms=None)
        outcomes = tuple(replace(o, latency_ms=None) for o in cfg.outcomes)
        parts.append((summary, outcomes))
    return parts


def test_retrieve_is_called_once_per_question_in_file_order() -> None:
    calls: list[tuple[str, UserProfile]] = []

    def retrieve(text: str, profile: UserProfile) -> list[RetrievalResult]:
        calls.append((text, profile))
        return []

    questions = [question("q1"), question("q2"), question("q3")]
    run_evaluation(questions, [Configuration(name="only", retrieve=retrieve)])

    assert calls == [(q.question, q.profile) for q in questions]


def test_outcomes_carry_the_returned_results_in_order() -> None:
    returned = [result("x"), result("a"), result("y")]
    run = run_evaluation([question("q1")], [config("c", returned)])

    (outcome,) = run.configurations[0].outcomes
    assert outcome.question_id == "q1"
    assert outcome.configuration == "c"
    assert outcome.results == tuple(returned)


def test_latency_is_recorded_for_each_call() -> None:
    run = run_evaluation([question("q1"), question("q2")], [config("c", [result("a")])])

    cfg = run.configurations[0]
    assert all(o.latency_ms is not None and o.latency_ms >= 0 for o in cfg.outcomes)
    assert cfg.summary.latency_p50_ms is not None
    assert cfg.summary.latency_p95_ms is not None


def test_run_metadata() -> None:
    run = run_evaluation(
        [question("q1"), question("q2")], [config("c", [])], k=3, question_file="qs.jsonl"
    )
    assert run.k == 3
    assert run.question_file == "qs.jsonl"
    assert run.question_count == 2


def test_default_k_is_five() -> None:
    assert run_evaluation([question("q1")], [config("c", [])]).k == 5


def test_summary_metrics() -> None:
    questions = [
        question("q1", expected_document="a"),  # hit at rank 1
        question("q2", expected_document="a"),  # miss (empty list)
        question("q3", expected_document=None, should_refuse=True),  # no expected document
    ]

    def retrieve(text: str, profile: UserProfile) -> list[RetrievalResult]:
        return [result("a")] if text == "text of q1" else []

    run = run_evaluation(questions, [Configuration(name="c", retrieve=retrieve)])

    summary = run.configurations[0].summary
    assert summary.name == "c"
    assert (summary.hit_rate.numerator, summary.hit_rate.denominator) == (1, 2)
    assert (summary.mrr.numerator, summary.mrr.denominator) == (1.0, 2)
    assert summary.section_hit_rate.value is None
    assert summary.cross_entitlement_total == 0
    assert summary.error_count == 0


def test_k_limits_both_hit_and_reciprocal_rank() -> None:
    returned = [result("x"), result("y"), result("a")]
    narrow = run_evaluation([question("q1")], [config("c", returned)], k=2)
    wide = run_evaluation([question("q1")], [config("c", returned)], k=3)

    (narrow_outcome,) = narrow.configurations[0].outcomes
    (wide_outcome,) = wide.configurations[0].outcomes
    assert narrow_outcome.document_hit is False
    assert wide_outcome.document_hit is True
    assert narrow_outcome.reciprocal_rank == 0.0
    assert wide_outcome.reciprocal_rank == pytest.approx(1 / 3)


def test_section_hit_is_recorded() -> None:
    questions = [question("q1", expected_section="s1")]
    run = run_evaluation(questions, [config("c", [result("a", "s1")])])
    (outcome,) = run.configurations[0].outcomes
    assert outcome.section_hit is True
    assert run.configurations[0].summary.section_hit_rate.value == 1.0


def test_cross_entitlement_results_are_counted() -> None:
    questions = [question("q1", not_entitled=("secret",))]
    returned = [result("a"), result("secret"), result("secret")]
    run = run_evaluation(questions, [config("c", returned)])

    (outcome,) = run.configurations[0].outcomes
    assert outcome.cross_entitlement_count == 2
    assert run.configurations[0].summary.cross_entitlement_total == 2


def test_empty_result_list_is_a_miss_and_the_run_continues() -> None:
    run = run_evaluation([question("q1"), question("q2")], [config("c", [])])
    outcomes = run.configurations[0].outcomes
    assert [o.document_hit for o in outcomes] == [False, False]
    assert [o.reciprocal_rank for o in outcomes] == [0.0, 0.0]


@pytest.mark.parametrize("bad_k", [0, -1])
def test_k_below_one_is_rejected(bad_k: int) -> None:
    with pytest.raises(ValueError, match="k"):
        run_evaluation([question("q1")], [config("c", [])], k=bad_k)


def test_empty_question_list_is_rejected() -> None:
    with pytest.raises(ValueError, match="question"):
        run_evaluation([], [config("c", [])])


def test_empty_configuration_list_is_rejected() -> None:
    with pytest.raises(ValueError, match="configuration"):
        run_evaluation([question("q1")], [])


def test_identical_inputs_give_identical_results_except_latency() -> None:
    questions = [question("q1", expected_section="s1"), question("q2", not_entitled=("secret",))]
    returned = [result("a", "s1"), result("secret")]

    first = run_evaluation(questions, [config("c", returned)], k=3)
    second = run_evaluation(questions, [config("c", returned)], k=3)

    assert normalized(first) == normalized(second)
