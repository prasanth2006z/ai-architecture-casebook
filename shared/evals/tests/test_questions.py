"""Tests for loading and validating question files (contracts/question-file.md).

All questions here are synthetic.
"""

import json
from pathlib import Path

import pytest

from evals.questions import QuestionFileError, load_questions


def valid(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": "q1",
        "question": "How many days of synthetic leave do I get?",
        "profile": {"country": "DE", "grade_band": "L3"},
        "expected_document": "leave-policy",
        "expected_section": "parental-leave",
        "should_refuse": False,
        "not_entitled_documents": ["exec-comp-policy"],
    }
    base.update(overrides)
    return base


def write(tmp_path: Path, *lines: object) -> Path:
    path = tmp_path / "questions.jsonl"
    path.write_text(
        "\n".join(line if isinstance(line, str) else json.dumps(line) for line in lines) + "\n",
        encoding="utf-8",
    )
    return path


def expect_error(path: Path, *fragments: str) -> None:
    with pytest.raises(QuestionFileError) as info:
        load_questions(path)
    message = str(info.value)
    for fragment in fragments:
        assert fragment in message, f"{fragment!r} not in {message!r}"


def test_valid_file_loads(tmp_path: Path) -> None:
    path = write(tmp_path, valid(), valid(id="q2", expected_section=None))
    questions = load_questions(path)
    assert [q.id for q in questions] == ["q1", "q2"]
    assert questions[0].profile.country == "DE"
    assert questions[0].not_entitled_documents == ("exec-comp-policy",)
    assert questions[1].expected_section is None


def test_blank_lines_are_ignored(tmp_path: Path) -> None:
    path = write(tmp_path, valid(), "", "   ", valid(id="q2"))
    assert [q.id for q in load_questions(path)] == ["q1", "q2"]


def test_optional_keys_may_be_absent(tmp_path: Path) -> None:
    record = valid(should_refuse=True)
    del record["expected_document"]
    del record["expected_section"]
    (question,) = load_questions(write(tmp_path, record))
    assert question.expected_document is None
    assert question.expected_section is None


def test_refusal_question_may_have_null_expected_document(tmp_path: Path) -> None:
    (question,) = load_questions(write(tmp_path, valid(should_refuse=True, expected_document=None)))
    assert question.should_refuse is True


def test_file_not_found(tmp_path: Path) -> None:
    missing = tmp_path / "nope.jsonl"
    expect_error(missing, "nope.jsonl", "not found")


def test_unreadable_file(tmp_path: Path) -> None:
    # A directory cannot be read as a file on any platform.
    expect_error(tmp_path, tmp_path.name)


def test_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "questions.jsonl"
    path.write_text("\n\n", encoding="utf-8")
    expect_error(path, "questions.jsonl", "empty")


def test_invalid_json_names_the_line(tmp_path: Path) -> None:
    path = write(tmp_path, valid(), "{not json")
    expect_error(path, "questions.jsonl:2", "JSON")


def test_missing_field_names_file_line_id_and_field(tmp_path: Path) -> None:
    record = valid(id="q7")
    del record["profile"]
    path = write(tmp_path, valid(), record)
    expect_error(path, "questions.jsonl:2", 'id "q7"', '"profile"', "required")


def test_missing_nested_field(tmp_path: Path) -> None:
    path = write(tmp_path, valid(profile={"grade_band": "L3"}))
    expect_error(path, "questions.jsonl:1", 'id "q1"', '"profile.country"', "required")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", 7),
        ("question", ["a"]),
        ("should_refuse", "yes"),
        ("not_entitled_documents", "doc-a"),
        ("not_entitled_documents", ["doc-a", 3]),
        ("expected_document", 5),
        ("expected_section", 5),
        ("profile", "DE"),
    ],
)
def test_wrong_type(tmp_path: Path, field: str, value: object) -> None:
    path = write(tmp_path, valid(**{field: value}))
    expect_error(path, "questions.jsonl:1", f'"{field}"')


@pytest.mark.parametrize("field", ["id", "question"])
def test_empty_string_is_rejected(tmp_path: Path, field: str) -> None:
    path = write(tmp_path, valid(**{field: ""}))
    expect_error(path, "questions.jsonl:1", f'"{field}"')


def test_non_object_line(tmp_path: Path) -> None:
    path = write(tmp_path, "[1, 2]")
    expect_error(path, "questions.jsonl:1", "object")


def test_duplicate_id(tmp_path: Path) -> None:
    path = write(tmp_path, valid(), valid())
    expect_error(path, "questions.jsonl:2", 'id "q1"', '"id"', "duplicate")


def test_unknown_key(tmp_path: Path) -> None:
    path = write(tmp_path, valid(expected_docment="typo"))
    expect_error(path, "questions.jsonl:1", '"expected_docment"', "unknown")


def test_null_expected_document_on_non_refusal_question(tmp_path: Path) -> None:
    path = write(tmp_path, valid(expected_document=None, should_refuse=False))
    expect_error(path, "questions.jsonl:1", 'id "q1"', '"expected_document"')
