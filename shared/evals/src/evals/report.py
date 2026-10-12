"""Markdown results table and JSON results file (research R9, contracts/results-file.md)."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
from typing import Any

from evals.models import (
    ConfigurationSummary,
    EvaluationRun,
    OutcomeError,
    QuestionOutcome,
    Rate,
)

NO_QUESTIONS_WITH_EXPECTED_DOCUMENT = "no question has an expected document"
NO_SECTIONS = "no result carries a section, or no question has an expected section"
NO_LATENCIES = "no successful retrieval calls"

Cell = tuple[str, str | None]  # (text, reason shown in the notes when the text is "n/a")
Column = tuple[str, Callable[[ConfigurationSummary], Cell]]


# --- Markdown ----------------------------------------------------------------------------


def render_markdown(run: EvaluationRun) -> str:
    """Render the results table, a footer, and a notes line for each "n/a" cell."""
    columns = _columns(run.k)
    header = ["Configuration", *(title for title, _ in columns)]
    lines = [_row(header), _row(["---"] * len(header))]
    notes: list[str] = []
    for configuration in run.configurations:
        summary = configuration.summary
        cells = [(summary.name, None)] + [(build(summary)) for _, build in columns]
        lines.append(_row([text for text, _ in cells]))
        for (title, _), (text, reason) in zip(columns, cells[1:], strict=True):
            if text == "n/a" and reason:
                notes.append(f"- {title} ({summary.name}): n/a, {reason}")
    lines += ["", _footer(run)]
    if notes:
        lines += ["", "Notes:", *notes]
    return "\n".join(lines) + "\n"


def _columns(k: int) -> list[Column]:
    return [
        (f"Hit@{k}", lambda s: _percent(s.hit_rate, NO_QUESTIONS_WITH_EXPECTED_DOCUMENT)),
        (f"Section hit@{k}", lambda s: _percent(s.section_hit_rate, NO_SECTIONS)),
        (f"MRR@{k}", lambda s: _decimal(s.mrr, NO_QUESTIONS_WITH_EXPECTED_DOCUMENT)),
        ("Cross-entitlement", lambda s: (str(s.cross_entitlement_total), None)),
        ("Latency p50 (ms)", lambda s: _latency(s.latency_p50_ms)),
        ("Latency p95 (ms)", lambda s: _latency(s.latency_p95_ms)),
        ("Errors", lambda s: (str(s.error_count), None)),
    ]


def _row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def _footer(run: EvaluationRun) -> str:
    noun = "question" if run.question_count == 1 else "questions"
    return f"k = {run.k}, {run.question_count} {noun}, {run.question_file}"


def _percent(rate: Rate, reason: str) -> Cell:
    value = rate.value
    return ("n/a", reason) if value is None else (f"{value * 100:.1f}%", None)


def _decimal(rate: Rate, reason: str) -> Cell:
    value = rate.value
    return ("n/a", reason) if value is None else (f"{value:.3f}", None)


def _latency(value: float | None) -> Cell:
    return ("n/a", NO_LATENCIES) if value is None else (f"{value:.1f}", None)


# --- JSON --------------------------------------------------------------------------------


def write_results_json(run: EvaluationRun, path: Path) -> None:
    """Write per-question outcomes, sorted keys, two-space indent, no timestamps."""
    data = {
        "k": run.k,
        "question_file": run.question_file,
        "question_count": run.question_count,
        "configurations": [
            {
                "name": configuration.summary.name,
                "summary": _summary_dict(configuration.summary),
                "outcomes": [_outcome_dict(o) for o in configuration.outcomes],
            }
            for configuration in run.configurations
        ],
    }
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _rate_dict(rate: Rate) -> dict[str, Any]:
    return {"value": rate.value, "numerator": rate.numerator, "denominator": rate.denominator}


def _summary_dict(summary: ConfigurationSummary) -> dict[str, Any]:
    return {
        "hit_rate": _rate_dict(summary.hit_rate),
        "section_hit_rate": _rate_dict(summary.section_hit_rate),
        "mrr": _rate_dict(summary.mrr),
        "cross_entitlement_total": summary.cross_entitlement_total,
        "latency_p50_ms": summary.latency_p50_ms,
        "latency_p95_ms": summary.latency_p95_ms,
        "error_count": summary.error_count,
        "correct_refusal_rate": _rate_dict(summary.correct_refusal_rate),
        "false_refusal_rate": _rate_dict(summary.false_refusal_rate),
        "citation_validity": _rate_dict(summary.citation_validity),
    }


def _error_dict(error: OutcomeError | None) -> dict[str, str] | None:
    return None if error is None else asdict(error)


def _outcome_dict(outcome: QuestionOutcome) -> dict[str, Any]:
    return {
        "question_id": outcome.question_id,
        "results": [asdict(result) for result in outcome.results],
        "document_hit": outcome.document_hit,
        "section_hit": outcome.section_hit,
        "reciprocal_rank": outcome.reciprocal_rank,
        "cross_entitlement_count": outcome.cross_entitlement_count,
        "latency_ms": outcome.latency_ms,
        "refused": outcome.refused,
        "refusal_correct": outcome.refusal_correct,
        "false_refusal": outcome.false_refusal,
        "citations_valid": outcome.citations_valid,
        "error": _error_dict(outcome.error),
    }
