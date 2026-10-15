"""Sidecar metadata for every policy (task T020)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from hr_dataset.catalog import build_catalog
from hr_dataset.cli import build

KEYS = {
    "allowed_countries",
    "allowed_grades",
    "document_id",
    "effective_date",
    "status",
    "synthetic",
    "title",
    "version",
}
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CODE_LINE = re.compile(r"^Policy code: (\S+) · Version (\S+) · Effective (\S+)$", re.M)


@pytest.fixture(scope="module")
def policies_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("dataset")
    build(out)
    return out / "policies"


@pytest.fixture(scope="module")
def sidecars(policies_dir: Path) -> dict[str, dict[str, object]]:
    found = {}
    for path in sorted(policies_dir.glob("*.md.metadata.json")):
        document_id = path.name.removesuffix(".md.metadata.json")
        found[document_id] = json.loads(path.read_text(encoding="utf-8"))
    assert found, "no sidecar files were written"
    return found


def test_every_markdown_has_one_sidecar_and_vice_versa(
    policies_dir: Path, sidecars: dict[str, dict[str, object]]
) -> None:
    markdown = {p.name.removesuffix(".md") for p in policies_dir.glob("*.md")}
    assert markdown == set(sidecars)
    assert len(markdown) >= 45


def test_sidecar_shape_and_field_rules(sidecars: dict[str, dict[str, object]]) -> None:
    for document_id, sidecar in sidecars.items():
        assert list(sidecar) == ["metadataAttributes"], document_id
        attrs = sidecar["metadataAttributes"]
        assert isinstance(attrs, dict)
        assert set(attrs) == KEYS, document_id
        assert attrs["document_id"] == document_id
        assert attrs["title"]
        countries, grades = attrs["allowed_countries"], attrs["allowed_grades"]
        assert isinstance(countries, list) and countries and set(countries) <= {"UK", "IN"}
        assert isinstance(grades, list) and grades and set(grades) <= {"G1-6", "G7+"}
        assert attrs["status"] in {"current", "superseded"}
        assert ISO_DATE.match(str(attrs["effective_date"])), document_id
        assert attrs["synthetic"] is True
        assert re.match(r"^\d+\.\d+$", str(attrs["version"])), document_id


def test_one_current_document_per_policy_family(sidecars: dict[str, dict[str, object]]) -> None:
    families: dict[str, list[str]] = {}
    for document_id, sidecar in sidecars.items():
        attrs = sidecar["metadataAttributes"]
        assert isinstance(attrs, dict)
        family = document_id.removesuffix("-v1")
        if attrs["status"] == "current":
            families.setdefault(family, []).append(document_id)
    all_families = {i.removesuffix("-v1") for i in sidecars}
    assert set(families) == all_families
    assert all(len(ids) == 1 for ids in families.values())


def test_superseded_is_older_than_its_current_version(
    sidecars: dict[str, dict[str, object]],
) -> None:
    superseded = [i for i in sidecars if i.endswith("-v1")]
    assert len(superseded) == 4
    for document_id in superseded:
        old = sidecars[document_id]["metadataAttributes"]
        new = sidecars[document_id.removesuffix("-v1")]["metadataAttributes"]
        assert isinstance(old, dict) and isinstance(new, dict)
        assert old["status"] == "superseded" and new["status"] == "current"
        assert old["effective_date"] < new["effective_date"]
        assert float(str(old["version"])) < float(str(new["version"]))


def test_code_version_date_line_matches_sidecar(
    policies_dir: Path, sidecars: dict[str, dict[str, object]]
) -> None:
    codes = {p.metadata.document_id: p.policy_code for p in build_catalog()}
    for document_id, sidecar in sidecars.items():
        attrs = sidecar["metadataAttributes"]
        assert isinstance(attrs, dict)
        text = (policies_dir / f"{document_id}.md").read_text(encoding="utf-8")
        match = CODE_LINE.search(text)
        assert match is not None, document_id
        assert match.groups() == (codes[document_id], attrs["version"], attrs["effective_date"])
