"""Security tests for the cross-entitlement check (Principle II).

These tests try to violate the check. They target the T008 signature; the implementation
is written by the repository author (T010). All document ids are synthetic.
"""

from types import SimpleNamespace

from evals.entitlement import EntitlementCheck, check_entitlements
from evals.models import RetrievalResult


def result(document_id: str, chunk_id: str = "c1") -> RetrievalResult:
    return RetrievalResult(document_id=document_id, chunk_id=chunk_id, score=0.5)


def check(results: list[object], forbidden: list[str]) -> EntitlementCheck:
    return check_entitlements(results, forbidden)


def test_forbidden_document_at_rank_1_counts() -> None:
    outcome = check([result("exec-comp"), result("leave")], ["exec-comp"])
    assert outcome == EntitlementCheck(cross_entitlement_count=1, unverifiable_count=0)


def test_forbidden_document_beyond_any_k_counts() -> None:
    results: list[object] = [result(f"doc-{i}", f"c{i}") for i in range(19)]
    results.append(result("exec-comp", "c20"))
    assert check(results, ["exec-comp"]).cross_entitlement_count == 1


def test_forbidden_document_that_is_also_expected_still_counts() -> None:
    # The check knows nothing about the expected document, so it cannot be excused by it.
    assert check([result("leave-policy")], ["leave-policy"]).cross_entitlement_count == 1


def test_matching_is_case_sensitive() -> None:
    assert check([result("doc-a")], ["Doc-A"]).cross_entitlement_count == 0


def test_whitespace_is_not_trimmed() -> None:
    assert check([result("doc-a ")], ["doc-a"]).cross_entitlement_count == 0
    assert check([result("doc-a")], [" doc-a"]).cross_entitlement_count == 0


def test_two_forbidden_results_count_as_two() -> None:
    results: list[object] = [result("exec-comp", "c1"), result("exec-comp", "c2")]
    assert check(results, ["exec-comp"]).cross_entitlement_count == 2


def test_different_forbidden_documents_each_count() -> None:
    results: list[object] = [result("a"), result("b"), result("c")]
    assert check(results, ["a", "c"]).cross_entitlement_count == 2


def test_no_forbidden_results_gives_zero() -> None:
    assert check([result("leave")], ["exec-comp"]) == EntitlementCheck(0, 0)


def test_empty_results_give_zero() -> None:
    assert check([], ["exec-comp"]) == EntitlementCheck(0, 0)


def test_empty_forbidden_list_gives_zero_for_verifiable_results() -> None:
    assert check([result("leave")], []) == EntitlementCheck(0, 0)


def test_empty_document_id_fails_closed() -> None:
    outcome = check([result("")], ["exec-comp"])
    assert outcome == EntitlementCheck(cross_entitlement_count=1, unverifiable_count=1)


def test_missing_document_id_fails_closed() -> None:
    outcome = check([SimpleNamespace(chunk_id="c1", score=0.5)], ["exec-comp"])
    assert outcome == EntitlementCheck(cross_entitlement_count=1, unverifiable_count=1)


def test_none_document_id_fails_closed() -> None:
    outcome = check([SimpleNamespace(document_id=None, chunk_id="c1")], ["exec-comp"])
    assert outcome == EntitlementCheck(cross_entitlement_count=1, unverifiable_count=1)


def test_non_text_document_id_fails_closed() -> None:
    outcome = check([SimpleNamespace(document_id=42, chunk_id="c1")], ["exec-comp"])
    assert outcome == EntitlementCheck(cross_entitlement_count=1, unverifiable_count=1)


def test_unverifiable_result_is_counted_even_with_empty_forbidden_list() -> None:
    # Entitlement cannot be verified, so it does not depend on the list.
    assert check([result("")], []) == EntitlementCheck(1, 1)


def test_other_results_are_still_checked_alongside_an_unverifiable_one() -> None:
    results: list[object] = [result(""), result("exec-comp"), result("leave")]
    outcome = check(results, ["exec-comp"])
    assert outcome == EntitlementCheck(cross_entitlement_count=2, unverifiable_count=1)


def test_inputs_are_not_mutated() -> None:
    results: list[object] = [result("exec-comp"), result("")]
    forbidden = ["exec-comp"]
    results_before = list(results)
    forbidden_before = list(forbidden)
    check(results, forbidden)
    assert results == results_before
    assert forbidden == forbidden_before
