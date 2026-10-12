"""Tests for the metric calculations (spec FR-005, FR-005a, FR-006, FR-008).

All identifiers are synthetic.
"""

import pytest

from evals.metrics import (
    document_hit,
    hit_rate,
    mean_reciprocal_rank,
    percentile,
    reciprocal_rank,
    section_hit,
    section_hit_rate,
)
from evals.models import Rate, RetrievalResult


def r(document_id: str, section: str | None = None, chunk_id: str = "c") -> RetrievalResult:
    return RetrievalResult(document_id=document_id, chunk_id=chunk_id, score=0.5, section=section)


# --- document hit at k -------------------------------------------------------------------


def test_document_hit_when_expected_document_is_in_top_k() -> None:
    assert document_hit([r("x"), r("a")], "a", k=2) is True


def test_document_miss_when_expected_document_is_beyond_k() -> None:
    results = [r("x1"), r("x2"), r("x3"), r("x4"), r("x5"), r("a")]
    assert document_hit(results, "a", k=5) is False
    assert document_hit(results, "a", k=6) is True


def test_fewer_results_than_k_are_not_padded() -> None:
    assert document_hit([r("a")], "a", k=5) is True
    assert document_hit([r("a")], "b", k=5) is False


def test_empty_result_list_is_a_miss() -> None:
    assert document_hit([], "a", k=5) is False


def test_document_hit_is_none_without_an_expected_document() -> None:
    assert document_hit([r("a")], None, k=5) is None


# --- reciprocal rank at k ----------------------------------------------------------------


def test_reciprocal_rank_of_first_position_is_one() -> None:
    assert reciprocal_rank([r("a"), r("x")], "a", k=5) == 1.0


def test_reciprocal_rank_of_third_position() -> None:
    assert reciprocal_rank([r("x"), r("y"), r("a")], "a", k=5) == pytest.approx(1 / 3)


def test_reciprocal_rank_uses_the_first_match() -> None:
    assert reciprocal_rank([r("x"), r("a"), r("a")], "a", k=5) == 0.5


def test_reciprocal_rank_is_zero_when_absent_or_empty() -> None:
    assert reciprocal_rank([r("x")], "a", k=5) == 0.0
    assert reciprocal_rank([], "a", k=5) == 0.0


def test_reciprocal_rank_only_considers_the_top_k() -> None:
    # MRR@k uses the same cutoff as hit rate: rank 7 contributes 0 when k is 5.
    results = [r(f"x{i}") for i in range(6)] + [r("a")]
    assert reciprocal_rank(results, "a", k=5) == 0.0
    assert reciprocal_rank(results, "a", k=7) == pytest.approx(1 / 7)


def test_reciprocal_rank_at_exactly_rank_k_counts() -> None:
    results = [r(f"x{i}") for i in range(4)] + [r("a")]
    assert reciprocal_rank(results, "a", k=5) == pytest.approx(1 / 5)


def test_reciprocal_rank_agrees_with_document_hit() -> None:
    results = [r("x"), r("y"), r("a")]
    for k in (1, 2, 3, 4):
        hit = document_hit(results, "a", k=k)
        assert (reciprocal_rank(results, "a", k=k) > 0) is hit  # type: ignore[operator]


def test_reciprocal_rank_is_none_without_an_expected_document() -> None:
    assert reciprocal_rank([r("a")], None, k=5) is None


# --- section hit at k --------------------------------------------------------------------


def test_section_hit_needs_document_and_section() -> None:
    assert section_hit([r("a", "s1")], "a", "s1", k=5) is True


def test_document_hit_with_another_section_is_a_section_miss() -> None:
    assert section_hit([r("a", "other")], "a", "s1", k=5) is False


def test_right_section_in_another_document_does_not_match() -> None:
    assert section_hit([r("b", "s1")], "a", "s1", k=5) is False


def test_result_without_a_section_never_matches() -> None:
    assert section_hit([r("a", None)], "a", "s1", k=5) is False


def test_section_hit_beyond_k_is_a_miss() -> None:
    results = [r("x"), r("x"), r("a", "s1")]
    assert section_hit(results, "a", "s1", k=2) is False
    assert section_hit(results, "a", "s1", k=3) is True


def test_section_hit_is_none_without_an_expected_section_or_document() -> None:
    assert section_hit([r("a", "s1")], "a", None, k=5) is None
    assert section_hit([r("a", "s1")], None, "s1", k=5) is None


# --- aggregated rates --------------------------------------------------------------------


def test_hit_rate_excludes_questions_without_an_expected_document() -> None:
    rate = hit_rate([True, False, None, True])
    assert rate == Rate(numerator=2, denominator=3)
    assert rate.value == pytest.approx(2 / 3)


def test_rate_with_zero_denominator_has_no_value() -> None:
    assert hit_rate([None, None]).value is None
    assert hit_rate([]).value is None
    assert hit_rate([]) == Rate(numerator=0, denominator=0)


def test_section_hit_rate_excludes_questions_without_an_expected_section() -> None:
    rate = section_hit_rate([True, False, None], any_section_returned=True)
    assert rate == Rate(numerator=1, denominator=2)


def test_section_hit_rate_is_na_when_no_result_carries_a_section() -> None:
    rate = section_hit_rate([False, False], any_section_returned=False)
    assert rate == Rate(numerator=0, denominator=0)
    assert rate.value is None


def test_section_hit_rate_is_na_without_any_expected_section() -> None:
    assert section_hit_rate([None, None], any_section_returned=True).value is None


def test_mean_reciprocal_rank_averages_and_excludes_none() -> None:
    rate = mean_reciprocal_rank([1.0, 0.0, None, 0.5])
    assert rate == Rate(numerator=1.5, denominator=3)
    assert rate.value == 0.5


def test_mean_reciprocal_rank_with_no_questions_has_no_value() -> None:
    assert mean_reciprocal_rank([None]).value is None


# --- nearest-rank percentiles ------------------------------------------------------------


def test_percentile_of_a_single_value() -> None:
    assert percentile([5.0], 50) == 5.0
    assert percentile([5.0], 95) == 5.0


def test_percentile_uses_nearest_rank_index() -> None:
    # index = ceil(p/100 * n) - 1 on the sorted values
    assert percentile([3.0, 1.0, 2.0], 50) == 2.0  # ceil(1.5) - 1 = 1
    assert percentile([float(i) for i in range(1, 11)], 50) == 5.0  # ceil(5.0) - 1 = 4


def test_p95_equals_the_maximum_for_small_n() -> None:
    assert percentile([3.0, 1.0, 2.0], 95) == 3.0
    assert percentile([float(i) for i in range(1, 11)], 95) == 10.0


def test_p95_is_not_the_maximum_for_twenty_values() -> None:
    assert percentile([float(i) for i in range(1, 21)], 95) == 19.0  # ceil(19.0) - 1 = 18


def test_percentile_of_no_values_is_none() -> None:
    assert percentile([], 50) is None


def test_percentile_index_uses_integer_arithmetic() -> None:
    # 95 * 20 / 100 is exactly 19: no floating-point rounding can push the index up.
    assert percentile([float(i) for i in range(1, 21)], 95) == 19.0
    assert percentile([float(i) for i in range(1, 101)], 99) == 99.0
    assert percentile([float(i) for i in range(1, 4)], 1) == 1.0


@pytest.mark.parametrize("p", [0, -1, 101])
def test_percentile_rejects_out_of_range_p(p: int) -> None:
    with pytest.raises(ValueError, match="percentile"):
        percentile([1.0], p)
