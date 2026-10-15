"""Immutable data types for the synthetic HR policy dataset.

All content is synthetic (constitution Principle III).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Profile:
    """The asker: country and grade band, as they appear in verified token claims.

    `country`: one of UK, IN. `grade_band`: one of G1-6, G7+. Matching is exact and
    case-sensitive.
    """

    country: str
    grade_band: str


@dataclass(frozen=True)
class Metadata:
    """The sidecar fields of one policy document; the ground truth for entitlement and version.

    `document_id`: equals file stem; lower-case; `<topic>-<country>`, `<topic>-global`, or
    `<topic>-<country>-v1` for superseded.
    `allowed_countries`: subset of UK, IN; non-empty; both for global documents.
    `allowed_grades`: subset of G1-6, G7+; non-empty; [G7+] for restricted.
    `status`: current or superseded.
    `effective_date`: ISO date text; superseded version's date is earlier than its current
    version's.
    """

    document_id: str
    title: str
    allowed_countries: tuple[str, ...]
    allowed_grades: tuple[str, ...]
    version: str
    effective_date: str
    status: str


@dataclass(frozen=True)
class Policy:
    """One generated document: metadata plus what is needed to render it.

    `topic`: template key. `family`: topic + country (or topic for a global document); a
    current document and its superseded predecessor share a family.
    `condition_section`: section id that holds an eligibility condition separate from the
    entitlement it qualifies (for example "3.2"), or None.
    `values`: placeholder values for the template (all text).
    `injection_probe`: true for the one document that carries instruction-like test text.
    """

    metadata: Metadata
    topic: str
    family: str
    policy_code: str
    values: dict[str, str]
    condition_section: str | None = None
    injection_probe: bool = False
    restricted: bool = False


@dataclass(frozen=True)
class QuestionRecord:
    """One evaluation question in the key order of the harness question-file contract."""

    id: str
    question: str
    profile: Profile
    expected_document: str | None
    expected_section: str | None
    should_refuse: bool
    not_entitled_documents: tuple[str, ...]
