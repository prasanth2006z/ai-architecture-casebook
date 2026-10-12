"""Tests for the `evals run` command line (contracts/cli.md).

All identifiers are synthetic.
"""

import json
import socket
from pathlib import Path

import pytest

from evals.cli import main

SAMPLES = Path(__file__).resolve().parent.parent / "samples"
QUESTIONS = SAMPLES / "questions.jsonl"
SAMPLE_CONFIGS = SAMPLES / "sample_configs.py"

MODULE_SOURCE = """\
from evals.models import Configuration

cfg = Configuration(name="from-module", retrieve=lambda text, profile: [])


def make() -> Configuration:
    return Configuration(name="from-factory", retrieve=lambda text, profile: [])
"""


def run_cli(*args: str) -> int:
    return main(["run", *args])


def one_line(text: str) -> bool:
    return len(text.strip().splitlines()) == 1


def test_run_prints_table_and_writes_files(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out_dir = tmp_path / "out"
    code = run_cli(
        "--questions", str(QUESTIONS),
        "--config", f"{SAMPLE_CONFIGS}:semantic",
        "--out-dir", str(out_dir),
    )  # fmt: skip

    captured = capsys.readouterr()
    assert code == 0
    assert "| semantic" in captured.out
    markdown = (out_dir / "results.md").read_text(encoding="utf-8")
    assert markdown.strip() in captured.out
    data = json.loads((out_dir / "results.json").read_text(encoding="utf-8"))
    assert data["question_count"] == 3
    assert data["question_file"] == "questions.jsonl"


def test_out_dir_defaults_to_eval_results(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    code = run_cli("--questions", str(QUESTIONS), "--config", f"{SAMPLE_CONFIGS}:semantic")
    assert code == 0
    assert (tmp_path / "eval-results" / "results.md").is_file()
    assert (tmp_path / "eval-results" / "results.json").is_file()


def test_repeated_config_gives_one_row_each(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = run_cli(
        "--questions", str(QUESTIONS),
        "--config", f"{SAMPLE_CONFIGS}:semantic",
        "--config", f"{SAMPLE_CONFIGS}:hybrid",
        "--out-dir", str(tmp_path),
    )  # fmt: skip
    out = capsys.readouterr().out
    assert code == 0
    assert "| semantic" in out
    assert "| hybrid" in out


def test_k_option_changes_the_cutoff(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = run_cli(
        "--questions", str(QUESTIONS),
        "--config", f"{SAMPLE_CONFIGS}:semantic",
        "--k", "1",
        "--out-dir", str(tmp_path),
    )  # fmt: skip
    assert code == 0
    assert "Hit@1" in capsys.readouterr().out


def test_module_attr_spec_loads_a_configuration_and_a_factory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "poc_configs.py").write_text(MODULE_SOURCE, encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    code = run_cli(
        "--questions", str(QUESTIONS),
        "--config", "poc_configs:cfg",
        "--config", "poc_configs:make",
        "--out-dir", str(tmp_path / "out"),
    )  # fmt: skip
    out = capsys.readouterr().out
    assert code == 0
    assert "| from-module" in out
    assert "| from-factory" in out


def test_malformed_question_file_exits_2_with_one_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad = tmp_path / "bad.jsonl"
    bad.write_text('{"id": "q1"}\n', encoding="utf-8")
    code = run_cli("--questions", str(bad), "--config", f"{SAMPLE_CONFIGS}:semantic")

    captured = capsys.readouterr()
    assert code == 2
    assert one_line(captured.err)
    assert "bad.jsonl:1" in captured.err
    assert "Traceback" not in captured.err
    assert captured.out == ""


@pytest.mark.parametrize(
    "spec",
    [
        "no-such-file.py:semantic",
        "no_such_module_xyz:semantic",
        f"{SAMPLE_CONFIGS}:no_such_attribute",
        f"{SAMPLE_CONFIGS}",  # missing ':attr'
    ],
)
def test_unloadable_config_exits_2_with_one_line(
    spec: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = run_cli("--questions", str(QUESTIONS), "--config", spec, "--out-dir", str(tmp_path))

    captured = capsys.readouterr()
    assert code == 2
    assert one_line(captured.err)
    assert "Traceback" not in captured.err


def test_run_makes_no_network_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("the harness must not open sockets")

    monkeypatch.setattr(socket, "socket", forbidden)
    code = run_cli(
        "--questions", str(QUESTIONS),
        "--config", f"{SAMPLE_CONFIGS}:semantic",
        "--out-dir", str(tmp_path),
    )  # fmt: skip
    assert code == 0
