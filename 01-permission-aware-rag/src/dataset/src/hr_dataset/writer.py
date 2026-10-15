"""Deterministic file output: UTF-8, LF line endings, one trailing newline, sorted JSON keys."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path


def normalise(text: str) -> bytes:
    """Encode text as UTF-8 with LF endings and exactly one trailing newline."""
    unix = text.replace("\r\n", "\n").replace("\r", "\n")
    return (unix.rstrip("\n") + "\n").encode("utf-8")


def json_text(data: object) -> str:
    """Pretty JSON with sorted keys, two-space indent and no ASCII escaping."""
    return json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def write_tree(folder: Path, files: Mapping[str, str]) -> None:
    """Write `files` (name to text) into `folder`; remove files that are not in the set."""
    folder.mkdir(parents=True, exist_ok=True)
    for stale in sorted(p for p in folder.iterdir() if p.is_file() and p.name not in files):
        stale.unlink()
    for name in sorted(files):
        (folder / name).write_bytes(normalise(files[name]))
