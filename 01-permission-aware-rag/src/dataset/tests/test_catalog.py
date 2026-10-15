"""Corpus shape (task T010). Plan: data-model.md corpus plan."""

from __future__ import annotations

import pytest

from hr_dataset.catalog import build_catalog
from hr_dataset.models import Policy

AREAS = {
    "leave": ["annual-leave", "sick-leave", "public-holidays", "special-leave"],
    "parental leave": ["parental-leave", "adoption-leave", "carers-leave"],
    "travel": ["business-travel", "travel-booking", "relocation-standard"],
    "expenses": ["expense-claims", "meal-allowance", "mobile-reimbursement"],
    "remote work": ["remote-work", "home-office-equipment"],
    "benefits": ["health-insurance", "retirement-savings", "learning-budget"],
}
COUNTRY_TOPICS = [t for topics in AREAS.values() for t in topics]
RESTRICTED_TOPICS = ["exec-relocation", "exec-compensation", "exec-travel", "exec-health-screening"]
GLOBAL_TOPICS = ["code-of-conduct", "anti-harassment", "data-privacy-for-hr"]
SUPERSEDED_IDS = [
    "business-travel-uk-v1",
    "expense-claims-in-v1",
    "parental-leave-uk-v1",
    "remote-work-in-v1",
]


@pytest.fixture(scope="module")
def catalog() -> dict[str, Policy]:
    policies = build_catalog()
    assert policies, "catalog is empty"
    return {p.metadata.document_id: p for p in policies}


def test_document_count_is_in_range(catalog: dict[str, Policy]) -> None:
    assert 45 <= len(catalog) <= 55


def test_all_six_areas_present_for_both_countries(catalog: dict[str, Policy]) -> None:
    for area, topics in AREAS.items():
        for country in ("uk", "in"):
            assert any(f"{t}-{country}" in catalog for t in topics), (area, country)


def test_country_topics_exist_for_both_countries(catalog: dict[str, Policy]) -> None:
    assert len(COUNTRY_TOPICS) == 18
    for topic in COUNTRY_TOPICS:
        assert f"{topic}-uk" in catalog, topic
        assert f"{topic}-in" in catalog, topic
        assert catalog[f"{topic}-uk"].metadata.allowed_countries == ("UK",)
        assert catalog[f"{topic}-in"].metadata.allowed_countries == ("IN",)


def test_restricted_documents_are_g7_only(catalog: dict[str, Policy]) -> None:
    for topic in RESTRICTED_TOPICS:
        for country in ("uk", "in"):
            assert catalog[f"{topic}-{country}"].metadata.allowed_grades == ("G7+",)
    restricted = [p for p in catalog.values() if p.metadata.allowed_grades == ("G7+",)]
    assert len(restricted) == 8


def test_global_documents_include_both_countries_and_grades(catalog: dict[str, Policy]) -> None:
    for topic in GLOBAL_TOPICS:
        metadata = catalog[f"{topic}-global"].metadata
        assert set(metadata.allowed_countries) == {"UK", "IN"}
        assert set(metadata.allowed_grades) == {"G1-6", "G7+"}
    two_country = [p for p in catalog.values() if len(p.metadata.allowed_countries) == 2]
    assert len(two_country) == 3


def test_exactly_four_superseded_with_current_counterparts(catalog: dict[str, Policy]) -> None:
    superseded = sorted(i for i, p in catalog.items() if p.metadata.status == "superseded")
    assert superseded == sorted(SUPERSEDED_IDS)
    for document_id in superseded:
        assert document_id.endswith("-v1")
        assert catalog[document_id.removesuffix("-v1")].metadata.status == "current"


def test_ids_are_unique_lower_case_and_codes_unique() -> None:
    policies = build_catalog()
    ids = [p.metadata.document_id for p in policies]
    assert len(ids) == len(set(ids)) > 0
    assert all(i == i.lower() for i in ids)
    codes = [p.policy_code for p in policies]
    assert len(codes) == len(set(codes))
