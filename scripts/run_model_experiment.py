"""Run a model-specific HumanEval-X C++ experiment in an isolated run directory."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ollama_client import DEFAULT_OLLAMA_URL


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"
DEFAULT_RUNS_ROOT = ROOT_DIR / "experiments" / "humanevalx_cpp_runs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a model-specific experiment directory and run the CodeEval pipeline there."
    )
    parser.add_argument("--model", required=True, help="Ollama model name, for example qwen3-coder:latest.")
    parser.add_argument(
        "--prompt-version",
        default="baseline_prompt",
        help="Prompt version directory name. Defaults to baseline_prompt.",
    )
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=DEFAULT_RUNS_ROOT,
        help="Root directory for model-specific runs. Defaults to experiments/humanevalx_cpp_runs.",
    )
    parser.add_argument("--limit", type=int, default=10, help="Number of problems to prepare. Defaults to 10.")
    parser.add_argument("--start-index", type=int, default=0, help="Start index for dataset selection. Defaults to 0.")
    parser.add_argument("--temperature", type=float, default=0.0, help="Ollama temperature. Defaults to 0.0.")
    parser.add_argument("--compiler", default="g++", help="C++ compiler command or path. Defaults to g++.")
    parser.add_argument("--std", default="c++17", help="C++ standard for original validation. Defaults to c++17.")
    parser.add_argument(
        "--ollama-url",
        default=DEFAULT_OLLAMA_URL,
        help=f"Ollama base URL. Defaults to {DEFAULT_OLLAMA_URL}.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Pass --continue-on-error to run_pipeline.py.",
    )
    parser.add_argument(
        "--force-run",
        action="store_true",
        help="Allow reuse of an existing run directory.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned run directory and commands without executing anything.",
    )
    parser.add_argument(
        "--skip-prepare",
        action="store_true",
        help="Skip prepare_dataset.py and run only run_pipeline.py against the existing run directory.",
    )
    parser.add_argument(
        "--validate-original",
        action="store_true",
        help="Pass --validate-original to prepare_dataset.py.",
    )
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT_DIR).as_posix()
    except ValueError:
        return str(path)


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT_DIR / path


def sanitize_model_name(model: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", model)
    sanitized = re.sub(r"_+", "_", sanitized)
    sanitized = sanitized.strip("_")
    return sanitized or "model"


def script_command(script_name: str, *args: str) -> list[str]:
    return [sys.executable, str(SCRIPTS_DIR / script_name), *args]


def problem_ids_for_limit(limit: int) -> list[str]:
    return [f"problem_{index:03d}" for index in range(limit)]


def build_prepare_command(args: argparse.Namespace, run_dir: Path) -> list[str]:
    command = script_command(
        "prepare_dataset.py",
        "--limit",
        str(args.limit),
        "--start-index",
        str(args.start_index),
        "--experiment-dir",
        str(run_dir),
        "--force",
        "--compiler",
        args.compiler,
    )
    if args.validate_original:
        command.extend(["--validate-original", "--std", args.std])
    return command


def build_pipeline_command(args: argparse.Namespace, run_dir: Path) -> list[str]:
    command = script_command(
        "run_pipeline.py",
        "--problem-ids",
        *problem_ids_for_limit(args.limit),
        "--model",
        args.model,
        "--temperature",
        str(args.temperature),
        "--prompt-version",
        args.prompt_version,
        "--compiler",
        args.compiler,
        "--ollama-url",
        args.ollama_url,
        "--experiment-dir",
        str(run_dir),
    )
    if args.continue_on_error:
        command.append("--continue-on-error")
    return command


def run_metadata(args: argparse.Namespace, run_dir: Path, model_dir_name: str, commands: dict[str, list[str] | None]) -> dict[str, Any]:
    return {
        "model": args.model,
        "model_dir_name": model_dir_name,
        "prompt_version": args.prompt_version,
        "run_dir": display_path(run_dir),
        "limit": args.limit,
        "start_index": args.start_index,
        "temperature": args.temperature,
        "compiler": args.compiler,
        "std": args.std,
        "ollama_url": args.ollama_url,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "commands": commands,
    }


def write_metadata(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def print_command(label: str, command: list[str] | None) -> None:
    if command is None:
        print(f"{label}: skipped")
        return
    print(f"{label}:")
    print("  " + " ".join(command))


def execute_command(label: str, command: list[str]) -> int:
    print_command(label, command)
    result = subprocess.run(command, check=False, cwd=ROOT_DIR)
    if result.returncode != 0:
        print(f"{label} failed with exit code {result.returncode}")
    return result.returncode


def main() -> int:
    args = parse_args()
    runs_root = resolve_path(args.runs_root)
    model_dir_name = sanitize_model_name(args.model)
    run_dir = runs_root / args.prompt_version / model_dir_name

    prepare_command = None if args.skip_prepare else build_prepare_command(args, run_dir)
    pipeline_command = build_pipeline_command(args, run_dir)
    commands = {
        "prepare_dataset": prepare_command,
        "run_pipeline": pipeline_command,
    }

    print(f"model: {args.model}")
    print(f"model_dir_name: {model_dir_name}")
    print(f"run_dir: {display_path(run_dir)}")

    if args.dry_run:
        print()
        print("Dry-run: no directories will be created and no commands will be executed.")
        print_command("prepare_dataset", prepare_command)
        print_command("run_pipeline", pipeline_command)
        print(f"run_metadata: {display_path(run_dir / 'run_metadata.json')}")
        return 0

    if run_dir.exists() and not args.force_run:
        print("Run directory already exists:")
        print(f"  {display_path(run_dir)}")
        print("Use --force-run to overwrite/reuse it.")
        return 1

    run_dir.mkdir(parents=True, exist_ok=True)
    write_metadata(run_dir / "run_metadata.json", run_metadata(args, run_dir, model_dir_name, commands))

    if prepare_command is not None:
        prepare_status = execute_command("prepare_dataset", prepare_command)
        if prepare_status != 0:
            return prepare_status

    pipeline_status = execute_command("run_pipeline", pipeline_command)
    return pipeline_status


if __name__ == "__main__":
    raise SystemExit(main())
