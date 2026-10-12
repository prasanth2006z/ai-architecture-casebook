"""Shared evaluation harness for the AI Architecture Casebook.

Metric definitions and the entitlement rules are recorded in
docs/adr/ADR-001-eval-metric-definitions.md.
"""

from evals.models import (
    Answer,
    Configuration,
    EvaluationRun,
    Question,
    RetrievalResult,
    UserProfile,
)
from evals.questions import QuestionFileError, load_questions
from evals.report import render_markdown, write_results_json
from evals.runner import run_evaluation

__all__ = [
    "Answer",
    "Configuration",
    "EvaluationRun",
    "Question",
    "QuestionFileError",
    "RetrievalResult",
    "UserProfile",
    "load_questions",
    "render_markdown",
    "run_evaluation",
    "write_results_json",
]
