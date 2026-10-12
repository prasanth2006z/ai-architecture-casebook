"""Runs configurations over a question set and builds outcomes and summaries.

See specs/001-eval-harness/contracts/plugin-api.md. Error handling for failing functions
and unverifiable results is added in later tasks (T022, T033); answer metrics in T028.
"""

from __future__ import annotations

import time
from collections.abc import Sequence

from evals import metrics
from evals.entitlement import check_entitlements
from evals.models import (
    Configuration,
    ConfigurationResult,
    ConfigurationSummary,
    EvaluationRun,
    Question,
    QuestionOutcome,
    Rate,
)


def run_evaluation(
    questions: Sequence[Question],
    configurations: Sequence[Configuration],
    k: int = 5,
    question_file: str = "",
) -> EvaluationRun:
    """Evaluate every configuration on every question, in the order given."""
    if k < 1:
        raise ValueError(f"k must be at least 1, got {k}")
    if not questions:
        raise ValueError("at least one question is required")
    if not configurations:
        raise ValueError("at least one configuration is required")

    results = []
    for configuration in configurations:
        outcomes = tuple(_evaluate(question, configuration, k) for question in questions)
        results.append(
            ConfigurationResult(summary=_summarize(configuration.name, outcomes), outcomes=outcomes)
        )
    return EvaluationRun(
        k=k,
        question_file=question_file,
        question_count=len(questions),
        configurations=tuple(results),
    )


def _evaluate(question: Question, configuration: Configuration, k: int) -> QuestionOutcome:
    started = time.perf_counter()
    results = list(configuration.retrieve(question.question, question.profile))
    latency_ms = (time.perf_counter() - started) * 1000

    entitlement = check_entitlements(results, question.not_entitled_documents)
    return QuestionOutcome(
        question_id=question.id,
        configuration=configuration.name,
        results=tuple(results),
        document_hit=metrics.document_hit(results, question.expected_document, k),
        section_hit=metrics.section_hit(
            results, question.expected_document, question.expected_section, k
        ),
        reciprocal_rank=metrics.reciprocal_rank(results, question.expected_document, k),
        cross_entitlement_count=entitlement.cross_entitlement_count,
        latency_ms=latency_ms,
        refused=None,
        refusal_correct=None,
        false_refusal=None,
        citations_valid=None,
    )


def _summarize(name: str, outcomes: Sequence[QuestionOutcome]) -> ConfigurationSummary:
    any_section_returned = any(r.section is not None for o in outcomes for r in o.results)
    latencies = [o.latency_ms for o in outcomes if o.latency_ms is not None]
    no_rate = Rate(numerator=0, denominator=0)  # answer metrics arrive with T028
    return ConfigurationSummary(
        name=name,
        hit_rate=metrics.hit_rate([o.document_hit for o in outcomes]),
        section_hit_rate=metrics.section_hit_rate(
            [o.section_hit for o in outcomes], any_section_returned
        ),
        mrr=metrics.mean_reciprocal_rank([o.reciprocal_rank for o in outcomes]),
        cross_entitlement_total=sum(o.cross_entitlement_count for o in outcomes),
        latency_p50_ms=metrics.percentile(latencies, 50),
        latency_p95_ms=metrics.percentile(latencies, 95),
        error_count=sum(1 for o in outcomes if o.error is not None),
        correct_refusal_rate=no_rate,
        false_refusal_rate=no_rate,
        citation_validity=no_rate,
    )
