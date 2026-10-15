"""Deterministic file output (task T007)."""

from __future__ import annotations

from pathlib import Path

from hr_dataset.writer import json_text, write_tree


def test_text_is_utf8_lf_with_one_trailing_newline(tmp_path: Path) -> None:
    write_tree(tmp_path, {"a.md": "line one\r\nline two\n\n\n"})
    raw = (tmp_path / "a.md").read_bytes()
    assert b"\r" not in raw
    assert raw == b"line one\nline two\n"


def test_non_ascii_text_is_written_as_utf8(tmp_path: Path) -> None:
    write_tree(tmp_path, {"a.md": "£500 per day"})
    assert (tmp_path / "a.md").read_bytes() == "£500 per day\n".encode()


def test_json_has_sorted_keys_two_space_indent_and_no_ascii_escaping() -> None:
    text = json_text({"b": 1, "a": "£"})
    assert text == '{\n  "a": "£",\n  "b": 1\n}\n'


def test_same_content_gives_identical_bytes(tmp_path: Path) -> None:
    files = {"x.md": "hello", "y.json": json_text({"k": [1, 2]})}
    first, second = tmp_path / "one", tmp_path / "two"
    write_tree(first, files)
    write_tree(second, files)
    for name in files:
        assert (first / name).read_bytes() == (second / name).read_bytes()


def test_write_tree_removes_stale_files(tmp_path: Path) -> None:
    write_tree(tmp_path, {"keep.md": "k", "old.md": "o"})
    write_tree(tmp_path, {"keep.md": "k"})
    assert sorted(p.name for p in tmp_path.iterdir()) == ["keep.md"]
