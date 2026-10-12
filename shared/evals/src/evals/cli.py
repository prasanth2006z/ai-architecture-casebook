"""Command line entry point: `evals run` (contracts/cli.md).

Exit codes: 0 when the run completes (even if some questions errored), 2 for usage errors,
an unreadable or malformed question file, or a configuration that cannot be loaded. Error
messages go to stderr as a single line, without a traceback.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from evals.models import Configuration
from evals.questions import QuestionFileError, load_questions
from evals.report import render_markdown, write_results_json
from evals.runner import run_evaluation

DEFAULT_OUT_DIR = "eval-results"


class ConfigLoadError(Exception):
    """A --config spec that cannot be turned into a Configuration."""


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    questions_path = Path(args.questions)
    try:
        questions = load_questions(questions_path)
        configurations = [load_configuration(spec) for spec in args.config]
        run = run_evaluation(questions, configurations, k=args.k, question_file=questions_path.name)
    except (QuestionFileError, ConfigLoadError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    markdown = render_markdown(run)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.md").write_text(markdown, encoding="utf-8")
    write_results_json(run, out_dir / "results.json")
    print(markdown, end="")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="evals", description="Shared evaluation harness")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="evaluate configurations on a question file")
    run.add_argument("--questions", required=True, help="JSONL question file")
    run.add_argument(
        "--config",
        action="append",
        required=True,
        help="module:attr or path/to/file.py:attr; repeat for several configurations",
    )
    run.add_argument("--k", type=int, default=5, help="cutoff for hit rates (default 5)")
    run.add_argument(
        "--out-dir", default=DEFAULT_OUT_DIR, help="where to write results.md and results.json"
    )
    return parser


def load_configuration(spec: str) -> Configuration:
    """Load a Configuration from `module:attr` or `path/to/file.py:attr`.

    `attr` is a Configuration or a zero-argument function returning one.
    """
    source, separator, attr = spec.rpartition(":")
    if not separator or not source or not attr or "/" in attr or "\\" in attr:
        raise ConfigLoadError(f'config "{spec}" must look like module:attr or path/to/file.py:attr')
    module = _load_file(source) if source.endswith(".py") else _import_module(source)
    try:
        value = getattr(module, attr)
    except AttributeError:
        raise ConfigLoadError(f'"{attr}" not found in {source}') from None
    if isinstance(value, Configuration):
        return value
    if callable(value):
        try:
            value = value()
        except Exception as exc:
            raise ConfigLoadError(f'calling "{attr}" in {source} failed: {exc}') from None
        if isinstance(value, Configuration):
            return value
    raise ConfigLoadError(
        f'"{attr}" in {source} is not a Configuration or a function returning one'
    )


def _import_module(name: str) -> object:
    cwd = os.getcwd()
    added = cwd not in sys.path
    if added:
        sys.path.insert(0, cwd)
    try:
        return importlib.import_module(name)
    except Exception as exc:
        raise ConfigLoadError(f'cannot import module "{name}": {exc}') from None
    finally:
        if added and cwd in sys.path:
            sys.path.remove(cwd)


def _load_file(source: str) -> object:
    path = Path(source)
    if not path.is_file():
        raise ConfigLoadError(f"config file not found: {source}")
    module_name = f"_evals_config_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ConfigLoadError(f"cannot load config file: {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module  # needed by dataclasses in the loaded file
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        sys.modules.pop(module_name, None)
        raise ConfigLoadError(f"cannot load config file {source}: {exc}") from None
    return module


if __name__ == "__main__":
    sys.exit(main())
