"""Security tests for the entitlement rule (task T005). Fail until the author writes T008.

Expected lists are written by hand, not computed with the function under test.
"""

from __future__ import annotations

import copy

import pytest

from hr_dataset.entitlement import is_entitled, not_entitled_for
from hr_dataset.models import Metadata, Profile

BOTH = ("G1-6", "G7+")


def doc(
    document_id: str, countries: tuple[str, ...], grades: tuple[str, ...], status: str
) -> Metadata:
    return Metadata(
        document_id=document_id,
        title=f"Synthetic {document_id}",
        allowed_countries=countries,
        allowed_grades=grades,
        version="1.0",
        effective_date="2026-01-01",
        status=status,
    )


FIXTURE = [
    doc("annual-leave-uk", ("UK",), BOTH, "current"),
    doc("annual-leave-in", ("IN",), BOTH, "current"),
    doc("code-of-conduct-global", ("UK", "IN"), BOTH, "current"),
    doc("exec-relocation-uk", ("UK",), ("G7+",), "current"),
    doc("exec-relocation-in", ("IN",), ("G7+",), "current"),
    doc("business-travel-uk-v1", ("UK",), BOTH, "superseded"),
]

GOLDEN = {
    ("UK", "G1-6"): ["annual-leave-in", "exec-relocation-in", "exec-relocation-uk"],
    ("UK", "G7+"): ["annual-leave-in", "exec-relocation-in"],
    ("IN", "G1-6"): [
        "annual-leave-uk",
        "business-travel-uk-v1",
        "exec-relocation-in",
        "exec-relocation-uk",
    ],
    ("IN", "G7+"): ["annual-leave-uk", "business-travel-uk-v1", "exec-relocation-uk"],
}


@pytest.mark.parametrize(("country", "grade"), list(GOLDEN))
def test_not_entitled_lists_match_hand_written_oracle(country: str, grade: str) -> None:
    assert not_entitled_for(Profile(country, grade), FIXTURE) == GOLDEN[(country, grade)]


def test_global_document_never_listed_for_a_country_it_includes() -> None:
    for country in ("UK", "IN"):
        for grade in BOTH:
            assert "code-of-conduct-global" not in not_entitled_for(
                Profile(country, grade), FIXTURE
            )


def test_entitlement_needs_both_country_and_grade() -> None:
    restricted_uk = FIXTURE[3]
    assert is_entitled(Profile("UK", "G7+"), restricted_uk) is True
    assert is_entitled(Profile("UK", "G1-6"), restricted_uk) is False  # grade fails
    assert is_entitled(Profile("IN", "G7+"), restricted_uk) is False  # country fails
    assert is_entitled(Profile("IN", "G1-6"), restricted_uk) is False  # both fail


def test_matching_is_exact_and_case_sensitive() -> None:
    standard_uk = FIXTURE[0]
    assert is_entitled(Profile("uk", "G1-6"), standard_uk) is False
    assert is_entitled(Profile("UK", "g1-6"), standard_uk) is False
    assert is_entitled(Profile("UK ", "G1-6"), standard_uk) is False


def test_superseded_document_follows_the_same_rule() -> None:
    superseded = FIXTURE[5]
    assert is_entitled(Profile("UK", "G1-6"), superseded) is True
    assert is_entitled(Profile("IN", "G1-6"), superseded) is False


def test_inputs_are_not_mutated() -> None:
    before = copy.deepcopy(FIXTURE)
    shuffled = list(reversed(FIXTURE))
    result = not_entitled_for(Profile("UK", "G1-6"), shuffled)
    assert FIXTURE == before
    assert shuffled == list(reversed(before))
    assert result == sorted(result)
