"""Loading and strict validation of JSONL question files.

See specs/001-eval-harness/contracts/question-file.md.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from evals.models import Question, UserProfile

REQUIRED_KEYS = ("id", "question", "profile", "should_refuse", "not_entitled_documents")
OPTIONAL_KEYS = ("expected_document", "expected_section")

Fail = Callable[[str, str], Exception]


class QuestionFileError(Exception):
    """A question file problem, with a message naming the file, line, question and field."""


def load_questions(path: Path) -> list[Question]:
    """Load and validate a question file; raise QuestionFileError on any problem."""
    lines = _read_lines(path)
    questions: list[Question] = []
    seen_ids: set[str] = set()
    for line_number, text in lines:
        record = _parse_line(path, line_number, text)
        question = _build_question(path, line_number, record)
        if question.id in seen_ids:
            raise _error(path, line_number, question.id, "id", "duplicate question id")
        seen_ids.add(question.id)
        questions.append(question)
    if not questions:
        raise QuestionFileError(f"{path.name}: file is empty (no questions found)")
    return questions


def _read_lines(path: Path) -> list[tuple[int, str]]:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise QuestionFileError(f"{path.name}: file not found ({path})") from None
    except (OSError, UnicodeDecodeError) as exc:
        raise QuestionFileError(f"{path.name}: cannot read file ({exc})") from None
    return [(number, text) for number, text in enumerate(raw.splitlines(), 1) if text.strip()]


def _parse_line(path: Path, line_number: int, text: str) -> dict[str, Any]:
    try:
        record = json.loads(text)
    except json.JSONDecodeError as exc:
        raise QuestionFileError(
            f"{path.name}:{line_number}: invalid JSON ({exc.msg} at column {exc.colno})"
        ) from None
    if not isinstance(record, dict):
        raise QuestionFileError(f"{path.name}:{line_number}: each line must be a JSON object")
    return record


def _error(
    path: Path, line_number: int, question_id: object, field: str, problem: str
) -> Exception:
    label = f' (id "{question_id}")' if isinstance(question_id, str) and question_id else ""
    return QuestionFileError(f'{path.name}:{line_number}{label}: field "{field}" {problem}')


def _build_question(path: Path, line_number: int, record: dict[str, Any]) -> Question:
    question_id = record.get("id")

    def fail(field: str, problem: str) -> Exception:
        return _error(path, line_number, question_id, field, problem)

    for key in record:
        if key not in REQUIRED_KEYS + OPTIONAL_KEYS:
            raise fail(key, "is an unknown key")
    for key in REQUIRED_KEYS:
        if key not in record:
            raise fail(key, "is required")

    text_id = _non_empty_text(record, "id", fail)
    question_text = _non_empty_text(record, "question", fail)
    profile = _profile(record["profile"], fail)
    should_refuse = record["should_refuse"]
    if not isinstance(should_refuse, bool):
        raise fail("should_refuse", "must be true or false")
    not_entitled = record["not_entitled_documents"]
    if not isinstance(not_entitled, list) or not all(isinstance(d, str) for d in not_entitled):
        raise fail("not_entitled_documents", "must be a list of text values")
    expected_document = _optional_text(record, "expected_document", fail)
    expected_section = _optional_text(record, "expected_section", fail)
    if expected_document is None and not should_refuse:
        raise fail("expected_document", "may be null only when should_refuse is true")

    return Question(
        id=text_id,
        question=question_text,
        profile=profile,
        expected_document=expected_document,
        expected_section=expected_section,
        should_refuse=should_refuse,
        not_entitled_documents=tuple(not_entitled),
    )


def _non_empty_text(record: dict[str, Any], key: str, fail: Fail) -> str:
    value = record[key]
    if not isinstance(value, str) or not value:
        raise fail(key, "must be non-empty text")
    return value


def _optional_text(record: dict[str, Any], key: str, fail: Fail) -> str | None:
    value = record.get(key)
    if value is not None and not isinstance(value, str):
        raise fail(key, "must be text or null")
    return value


def _profile(value: object, fail: Fail) -> UserProfile:
    if not isinstance(value, dict):
        raise fail("profile", "must be an object with country and grade_band")
    for key in ("country", "grade_band"):
        if key not in value:
            raise fail(f"profile.{key}", "is required")
        if not isinstance(value[key], str) or not value[key]:
            raise fail(f"profile.{key}", "must be non-empty text")
    return UserProfile(country=value["country"], grade_band=value["grade_band"])
