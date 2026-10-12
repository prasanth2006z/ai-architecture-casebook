"""SECURITY-CRITICAL: author-written (constitution Principle VIII).

Counts cross-entitlement retrievals: returned results the asking user is not entitled
to see. Rules, from specs/001-eval-harness/research.md R7 and ADR-001:

- exact, case-sensitive match between a result's document id and the question's
  not-entitled list;
- every returned result is checked, regardless of rank or expected document;
- fail closed: a result with a missing, empty or non-text document id counts as a
  cross-entitlement retrieval and is also counted as unverifiable.

This module is a stub. The implementation is written by the repository author (task T010).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class EntitlementCheck:
    """Outcome of checking one question's returned results."""

    cross_entitlement_count: int
    unverifiable_count: int


def check_entitlements(
    results: Sequence[object], not_entitled_documents: Sequence[str]
) -> EntitlementCheck:
    """Count cross-entitlement retrievals among `results`.

    `results` are whatever a POC function returned, so items may be malformed.
    """
    forbidden = set(not_entitled_documents)  # lookup copy; the input list is not modified
    cross_entitlement_count = 0
    unverifiable_count = 0

    for result in results:
        doc_id = getattr(result, "document_id", None)  # malformed results may lack it

        if not isinstance(doc_id, str) or not doc_id:
            # Fail closed: we can't verify entitlement, so treat it as a leak.
            unverifiable_count += 1
            cross_entitlement_count += 1
            continue

        if doc_id in forbidden:  # exact, case-sensitive match
            cross_entitlement_count += 1

    return EntitlementCheck(
        cross_entitlement_count=cross_entitlement_count,
        unverifiable_count=unverifiable_count,
    )
