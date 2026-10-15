"""Command line for the dataset generator: `hr-dataset build`.

Contract: specs/002-hr-policy-dataset/contracts/cli.md.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from hr_dataset.catalog import CatalogError, build_catalog
from hr_dataset.models import Policy
from hr_dataset.render import RenderError, metadata_json, render_policy
from hr_dataset.writer import write_tree

DEFAULT_OUT = Path(__file__).resolve().parents[4] / "evals"


def policy_files(policies: Sequence[Policy]) -> dict[str, str]:
    """File name to text for every policy Markdown file and its metadata sidecar."""
    files: dict[str, str] = {}
    for policy in policies:
        name = f"{policy.metadata.document_id}.md"
        files[name] = render_policy(policy)
        files[f"{name}.metadata.json"] = metadata_json(policy)
    return files


def build(out: Path) -> int:
    """Render every policy and sidecar into `out/policies`; return the number of files written."""
    files = policy_files(build_catalog())
    write_tree(out / "policies", files)
    return len(files)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="hr-dataset", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build_parser = commands.add_parser("build", help="render policies and questions")
    build_parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    try:
        written = build(args.out)
    except (CatalogError, RenderError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {written} files to {args.out / 'policies'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
