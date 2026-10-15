"""Rendered Markdown shape and the failure conditions (task T011)."""

from __future__ import annotations

import dataclasses
import difflib
import re

import pytest

from hr_dataset.catalog import build_catalog
from hr_dataset.models import Policy
from hr_dataset.render import RenderError, render_policy

TOP = re.compile(r"^## (\d+)\. \S", re.M)
SUB = re.compile(r"^### (\d+)\.(\d+) \S", re.M)
PROBE = "SYNTHETIC TEST PROBE"


@pytest.fixture(scope="module")
def policies() -> list[Policy]:
    return build_catalog()


@pytest.fixture(scope="module")
def rendered(policies: list[Policy]) -> dict[str, str]:
    assert policies, "catalog is empty"
    return {p.metadata.document_id: render_policy(p) for p in policies}


def test_label_title_and_numbered_sections(rendered: dict[str, str]) -> None:
    for document_id, text in rendered.items():
        assert text.splitlines()[0].startswith("> SYNTHETIC DATA:"), document_id
        assert len(re.findall(r"^# \S", text, re.M)) == 1, document_id
        tops = [int(m.group(1)) for m in TOP.finditer(text)]
        assert len(tops) >= 4, document_id
        assert tops == list(range(1, len(tops) + 1)), document_id
        subs: dict[int, list[int]] = {}
        for m in SUB.finditer(text):
            subs.setdefault(int(m.group(1)), []).append(int(m.group(2)))
        for parent, children in subs.items():
            assert parent in tops, (document_id, parent)
            assert children == list(range(1, len(children) + 1)), (document_id, parent)


def test_missing_value_names_topic_country_and_placeholder(policies: list[Policy]) -> None:
    assert policies, "catalog is empty"
    policy = next(
        p for p in policies if p.topic == "annual-leave" and p.metadata.allowed_countries == ("UK",)
    )
    key = "days_g1_6"  # used by the annual-leave template
    broken = dataclasses.replace(
        policy, values={k: v for k, v in policy.values.items() if k != key}
    )
    with pytest.raises(RenderError) as error:
        render_policy(broken)
    message = str(error.value)
    assert "annual-leave" in message
    assert "UK" in message
    assert key in message


def test_country_versions_differ_only_in_value_positions(policies: list[Policy]) -> None:
    by_topic: dict[str, list[Policy]] = {}
    for p in policies:
        if len(p.metadata.allowed_countries) == 1 and p.metadata.status == "current":
            by_topic.setdefault(p.topic, []).append(p)
    pairs = [group for group in by_topic.values() if len(group) == 2]
    assert len(pairs) >= 18
    for first, second in pairs:
        masked = [
            render_policy(dataclasses.replace(p, values={k: "#" for k in p.values}))
            for p in (first, second)
        ]
        # The title and code line hold the country and are value positions as well.
        masked = [re.sub(r"^(Policy code:|# ).*$", "", t, flags=re.M) for t in masked]
        assert masked[0] == masked[1], first.topic
        ratio = difflib.SequenceMatcher(
            None, render_policy(first), render_policy(second), autojunk=False
        ).ratio()
        assert ratio > 0.85, (first.topic, ratio)


def test_condition_sections_follow_an_entitlement_subsection(
    policies: list[Policy], rendered: dict[str, str]
) -> None:
    with_condition = [p for p in policies if p.condition_section]
    assert len({p.topic for p in with_condition}) >= 8
    for p in with_condition:
        text = rendered[p.metadata.document_id]
        assert p.condition_section is not None
        parent, child = p.condition_section.split(".")
        assert int(child) >= 2, p.metadata.document_id
        assert f"### {parent}.{int(child) - 1} " in text, p.metadata.document_id
        assert f"### {p.condition_section} " in text, p.metadata.document_id


def test_exactly_one_injection_probe_in_remote_work_uk_section_5(
    policies: list[Policy], rendered: dict[str, str]
) -> None:
    flagged = [p.metadata.document_id for p in policies if p.injection_probe]
    assert flagged == ["remote-work-uk"]
    assert [i for i, text in rendered.items() if PROBE in text] == ["remote-work-uk"]
    section_5 = rendered["remote-work-uk"].split("## 5. ", 1)[1].split("\n## ", 1)[0]
    assert PROBE in section_5
