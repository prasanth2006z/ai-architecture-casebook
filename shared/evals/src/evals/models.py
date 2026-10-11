"""Immutable data types for the evaluation harness.

Field names match the JSON files. Constraints are quoted from
specs/001-eval-harness/data-model.md.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal

ErrorStage = Literal["retrieve", "answer", "validate"]


@dataclass(frozen=True)
class UserProfile:
    """The asking user's profile. `country` and `grade_band`: required, non-empty."""

    country: str
    grade_band: str


@dataclass(frozen=True)
class Question:
    """One evaluation item.

    `id`: required, non-empty, unique within the file.
    `expected_document`: null allowed only when `should_refuse` is true.
    `expected_section`: optional; null excludes the question from section hit rate.
    `not_entitled_documents`: required, may be empty.
    """

    id: str
    question: str
    profile: UserProfile
    expected_document: str | None
    expected_section: str | None
    should_refuse: bool
    not_entitled_documents: tuple[str, ...]


@dataclass(frozen=True)
class RetrievalResult:
    """One ranked item returned by a retrieval function.

    `document_id`: required and non-empty; a missing, empty, or non-string value fails
    closed: the result counts as a cross-entitlement retrieval and the question is
    recorded as an error.
    `section`: optional.
    """

    document_id: str
    chunk_id: str
    score: float
    section: str | None = None


@dataclass(frozen=True)
class Answer:
    """Optional output of an answer function. `text` may be empty when refused."""

    text: str
    cited_chunk_ids: tuple[str, ...]
    refused: bool


RetrieveFn = Callable[[str, UserProfile], list[RetrievalResult]]
AnswerFn = Callable[[str, UserProfile, list[RetrievalResult]], Answer]


@dataclass(frozen=True)
class Configuration:
    """A named variant of a POC. `name` must be unique within a run."""

    name: str
    retrieve: RetrieveFn
    answer: AnswerFn | None = None


@dataclass(frozen=True)
class OutcomeError:
    """A recorded failure. `stage` is one of retrieve, answer, validate."""

    stage: ErrorStage
    type: str
    message: str


@dataclass(frozen=True)
class QuestionOutcome:
    """Per-question, per-configuration record.

    `results`: as returned, in order; empty when the function raised; kept in full when a
    result had an unverifiable document id.
    `document_hit`: false for any errored question; None when the question has no
    expected document (excluded from the rate).
    `section_hit`: false for any errored question that has an expected section; None when
    no expected section; false when no returned result matches it.
    `reciprocal_rank`: 0 for any errored question that has an expected document; None
    when no expected document.
    `cross_entitlement_count`: across all returned results, including unverifiable ones.
    `latency_ms`: None for any errored question (excluded from percentiles).
    """

    question_id: str
    configuration: str
    results: tuple[RetrievalResult, ...]
    document_hit: bool | None
    section_hit: bool | None
    reciprocal_rank: float | None
    cross_entitlement_count: int
    latency_ms: float | None
    refused: bool | None
    refusal_correct: bool | None
    false_refusal: bool | None
    citations_valid: bool | None
    error: OutcomeError | None = None


@dataclass(frozen=True)
class Rate:
    """A rate with its parts. `value` is None when `denominator` is 0 (shown as n/a)."""

    numerator: float
    denominator: int

    @property
    def value(self) -> float | None:
        if self.denominator == 0:
            return None
        return self.numerator / self.denominator


@dataclass(frozen=True)
class ConfigurationSummary:
    """Per-configuration metrics, derived only from outcomes."""

    name: str
    hit_rate: Rate
    section_hit_rate: Rate
    mrr: Rate
    cross_entitlement_total: int
    latency_p50_ms: float | None
    latency_p95_ms: float | None
    error_count: int
    correct_refusal_rate: Rate
    false_refusal_rate: Rate
    citation_validity: Rate


@dataclass(frozen=True)
class ConfigurationResult:
    """A configuration's summary and all of its question outcomes."""

    summary: ConfigurationSummary
    outcomes: tuple[QuestionOutcome, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class EvaluationRun:
    """One run: a question file evaluated under N configurations."""

    k: int
    question_file: str
    question_count: int
    configurations: tuple[ConfigurationResult, ...]
