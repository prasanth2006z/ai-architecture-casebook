"""Renders a policy into Markdown from its template and value table, and its sidecar JSON.

Output format: specs/002-hr-policy-dataset/contracts/dataset-files.md. Templates use
string.Template and `substitute`, so a missing value fails the build instead of leaving a gap.
"""

from __future__ import annotations

import re
from pathlib import Path
from string import Template

from hr_dataset.models import Policy
from hr_dataset.writer import json_text

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"
LABEL = "> SYNTHETIC DATA: Globex Corp is a fictional company. This policy is invented for testing."
HEADING = re.compile(r"^#{2,3} (\d+(?:\.\d+)?)\.? \S", re.M)


class RenderError(Exception):
    """A template could not be rendered; the message names topic, country and placeholder."""


def render_policy(policy: Policy, templates_dir: Path = TEMPLATES_DIR) -> str:
    """The Markdown text of one policy."""
    path = templates_dir / f"{policy.topic}.md"
    where = f'topic "{policy.topic}" ({",".join(policy.metadata.allowed_countries)})'
    try:
        template = Template(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RenderError(f"{where}: cannot read template {path.name} ({exc})") from None
    try:
        body = template.substitute(policy.values)
    except KeyError as exc:
        raise RenderError(f'{where}: placeholder "{exc.args[0]}" has no value') from None
    except ValueError as exc:
        raise RenderError(f"{where}: bad placeholder in {path.name} ({exc})") from None
    metadata = policy.metadata
    header = (
        f"{LABEL}\n\n# {metadata.title}\n\n"
        f"Policy code: {policy.policy_code} · Version {metadata.version} · "
        f"Effective {metadata.effective_date}\n\n"
    )
    return header + body


def section_ids(markdown: str) -> list[str]:
    """Section ids in document order, for example ["1", "2", "3", "3.1", "3.2", "4"]."""
    return [match.group(1) for match in HEADING.finditer(markdown)]


def metadata_json(policy: Policy) -> str:
    """The sidecar text for one policy, in the Bedrock metadataAttributes shape."""
    metadata = policy.metadata
    return json_text(
        {
            "metadataAttributes": {
                "allowed_countries": list(metadata.allowed_countries),
                "allowed_grades": list(metadata.allowed_grades),
                "document_id": metadata.document_id,
                "effective_date": metadata.effective_date,
                "status": metadata.status,
                "synthetic": True,
                "title": metadata.title,
                "version": metadata.version,
            }
        }
    )
