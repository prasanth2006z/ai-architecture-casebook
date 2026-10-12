"""Metric calculations (evaluation core, Principle VIII: reviewed line by line by the author).

Per-question functions return None when the question is not part of the metric (for example
no expected document), so the aggregate functions can exclude it. Aggregates return a Rate,
whose value is None when its denominator is 0 (shown as "n/a" in reports).

Definitions are recorded in ADR-001.
"""

from __future__ import annotations

from collections.abc import Sequence

from evals.models import Rate, RetrievalResult

# --- per-question ------------------------------------------------------------------------


def document_hit(
    results: Sequence[RetrievalResult], expected_document: str | None, k: int
) -> bool | None:
    """True if the expected document is in the top k results; None without an expected document."""
    if expected_document is None:
        return None
    return any(result.document_id == expected_document for result in results[:k])


def section_hit(
    results: Sequence[RetrievalResult],
    expected_document: str | None,
    expected_section: str | None,
    k: int,
) -> bool | None:
    """True if a top-k result matches both the expected document and section.

    A result without a section never matches. None when the question has no expected
    document or no expected section.
    """
    if expected_document is None or expected_section is None:
        return None
    return any(
        result.document_id == expected_document and result.section == expected_section
        for result in results[:k]
    )


def reciprocal_rank(
    results: Sequence[RetrievalResult], expected_document: str | None, k: int
) -> float | None:
    """1 / rank of the first result from the expected document within the top k (MRR@k).

    0.0 when the document is not in the top k (including an empty list); None without an
    expected document. Uses the same cutoff as document_hit.
    """
    if expected_document is None:
        return None
    for position, result in enumerate(results[:k], start=1):
        if result.document_id == expected_document:
            return 1 / position
    return 0.0


# --- aggregates --------------------------------------------------------------------------


def hit_rate(hits: Sequence[bool | None]) -> Rate:
    """Share of True among the questions that have a hit value (None is excluded)."""
    counted = [hit for hit in hits if hit is not None]
    return Rate(numerator=sum(counted), denominator=len(counted))


def section_hit_rate(hits: Sequence[bool | None], any_section_returned: bool) -> Rate:
    """Like hit_rate, but "n/a" when no result in the configuration carried a section."""
    if not any_section_returned:
        return Rate(numerator=0, denominator=0)
    return hit_rate(hits)


def mean_reciprocal_rank(reciprocal_ranks: Sequence[float | None]) -> Rate:
    """Mean of the reciprocal ranks at k, excluding questions without an expected document."""
    counted = [value for value in reciprocal_ranks if value is not None]
    return Rate(numerator=sum(counted), denominator=len(counted))


def percentile(values: Sequence[float], p: int) -> float | None:
    """Nearest-rank percentile: the sorted value at index ceil(p * n / 100) - 1.

    `p` is a whole number from 1 to 100. The index uses integer arithmetic (ceiling
    division), so there is no floating-point rounding. None for no values. For small n,
    p95 therefore equals the maximum.
    """
    if not 0 < p <= 100:
        raise ValueError(f"percentile p must be from 1 to 100, got {p}")
    if not values:
        return None
    ordered = sorted(values)
    index = -(-p * len(ordered) // 100) - 1  # ceiling division
    return ordered[index]
