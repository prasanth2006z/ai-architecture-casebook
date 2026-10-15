"""Expands topics, countries and value tables into the list of policies.

Reads the TOML value tables under data/values/ (see data-model.md in the spec). No clock, no
environment lookups: dates and versions come from the tables, so the catalog is reproducible.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from hr_dataset.models import Metadata, Policy

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
COUNTRY_KEYS = ("uk", "in")
GRADE_KEYS = {"G1-6": "g1_6", "G7+": "g7_plus"}
ALL_GRADES = ("G1-6", "G7+")
SPECIAL_FILES = ("countries.toml", "superseded.toml")


class CatalogError(Exception):
    """A value table is incomplete or inconsistent; the message names the topic and field."""


def build_catalog(data_dir: Path = DATA_DIR) -> list[Policy]:
    """Every policy of the dataset, sorted by document id."""
    constants = _read(data_dir / "values" / "countries.toml")
    topics = _read_topics(data_dir / "values")
    current: dict[str, Policy] = {}
    for topic in sorted(topics):
        for policy in _policies_for_topic(topic, topics[topic], constants):
            current[policy.metadata.document_id] = policy
    superseded = _superseded(data_dir / "values" / "superseded.toml", current)
    return sorted([*current.values(), *superseded], key=lambda p: p.metadata.document_id)


def _read(path: Path) -> dict[str, Any]:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _read_topics(values_dir: Path) -> dict[str, dict[str, Any]]:
    topics: dict[str, dict[str, Any]] = {}
    for path in sorted(values_dir.glob("*.toml")):
        if path.name in SPECIAL_FILES:
            continue
        for topic, table in _read(path).items():
            if topic in topics:
                raise CatalogError(f'topic "{topic}" is defined twice (second time in {path.name})')
            topics[topic] = table
    return topics


def flatten(table: dict[str, Any]) -> dict[str, str]:
    """Text values of a table; grade-band tables become <key>_g1_6 and <key>_g7_plus."""
    out: dict[str, str] = {}
    for key, value in table.items():
        if isinstance(value, bool):
            continue
        if isinstance(value, dict):
            if not all(grade in value for grade in GRADE_KEYS):
                continue  # a country sub-table such as [topic.uk], not a grade-band value
            for grade, suffix in GRADE_KEYS.items():
                out[f"{key}_{suffix}"] = str(value[grade])
        elif isinstance(value, str | int):
            out[key] = str(value)
    return out


def _policies_for_topic(
    topic: str, table: dict[str, Any], constants: dict[str, Any]
) -> list[Policy]:
    scope = "global" if table.get("scope") == "global" else None
    keys = ("global",) if scope else COUNTRY_KEYS
    return [_policy(topic, table, key, constants) for key in keys]


def _policy(topic: str, table: dict[str, Any], key: str, constants: dict[str, Any]) -> Policy:
    country_table = table.get(key)
    if country_table is None:
        raise CatalogError(f'topic "{topic}" has no [{topic}.{key}] table')
    values = {**flatten(constants[key]), **flatten(table), **flatten(country_table)}
    version = _required(topic, key, values, "version")
    effective_date = _required(topic, key, values, "effective_date")
    code = _required(topic, key, values, "policy_code")
    title = _required(topic, key, values, "title")
    is_global = key == "global"
    countries = ("UK", "IN") if is_global else (key.upper(),)
    document_id = f"{topic}-{key}"
    restricted = bool(table.get("restricted", False))
    metadata = Metadata(
        document_id=document_id,
        title=title if is_global else f"{title} ({values['country']})",
        allowed_countries=countries,
        allowed_grades=("G7+",) if restricted else ALL_GRADES,
        version=version,
        effective_date=effective_date,
        status="current",
    )
    return Policy(
        metadata=metadata,
        topic=topic,
        family=document_id,
        policy_code=code,
        values=values,
        condition_section=table.get("condition_section"),
        injection_probe=bool(country_table.get("injection_probe", False)),
        restricted=restricted,
    )


def _required(topic: str, key: str, values: dict[str, str], field: str) -> str:
    if field not in values:
        raise CatalogError(f'topic "{topic}" ({key}): field "{field}" is required')
    return values[field]


def _superseded(path: Path, current: dict[str, Policy]) -> list[Policy]:
    found: list[Policy] = []
    for entry in _read(path).get("superseded", []):
        topic, key = entry["topic"], entry["country"]
        base = current.get(f"{topic}-{key}")
        if base is None:
            raise CatalogError(f'superseded entry "{topic}-{key}" has no current document')
        for field in ("version", "effective_date"):
            if field not in entry:
                raise CatalogError(f'superseded entry "{topic}-{key}": field "{field}" is required')
        values = {**base.values, **flatten(entry.get("overrides", {}))}
        metadata = Metadata(
            document_id=f"{base.metadata.document_id}-v1",
            title=base.metadata.title,
            allowed_countries=base.metadata.allowed_countries,
            allowed_grades=base.metadata.allowed_grades,
            version=entry["version"],
            effective_date=entry["effective_date"],
            status="superseded",
        )
        found.append(
            Policy(
                metadata=metadata,
                topic=topic,
                family=base.family,
                policy_code=f"{base.policy_code}-V1",
                values=values,
                condition_section=base.condition_section,
                restricted=base.restricted,
            )
        )
    return found
