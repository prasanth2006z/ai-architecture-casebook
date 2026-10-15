"""SECURITY-CRITICAL: author-written (constitution Principle VIII).

Decides which documents an asker may see; its output is the ground truth for the
not-entitled lists in the question file. Rule (spec FR-004a, FR-011; ADR-002): entitled
exactly when the asker's country is in `allowed_countries` and the asker's grade band is in
`allowed_grades`.

Stub only: the implementation is task T008 and is written by the repository author.
"""

from __future__ import annotations

from collections.abc import Sequence

from hr_dataset.models import Metadata, Profile


def is_entitled(profile: Profile, metadata: Metadata) -> bool:
    """True if the asker may see the document."""
    raise NotImplementedError("T008: written by the repository author")


def not_entitled_for(profile: Profile, all_metadata: Sequence[Metadata]) -> list[str]:
    """Sorted ids of every document in `all_metadata` the asker may not see."""
    raise NotImplementedError("T008: written by the repository author")
