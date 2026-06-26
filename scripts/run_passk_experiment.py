"""Run pass@1/pass@3 experiments with sample-isolated outputs."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ollama_client import DEFAULT_OLLAMA_URL


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"
DEFAULT_RUNS_ROOT = ROOT_DIR / "experiments" / "humanevalx_cpp_runs"
DEFAULT_PROMPT_VERSION = "prompt_v3_general_design"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run prompt_v3-style pass@1/pass@3 experiments with per-sample outputs."
    )
    parser.add_argument("--model", required=True, help="Ollama model name.")
    parser.add_argument(
        "--prompt-version",
        default=DEFAULT_PROMPT_VERSION,
        help=f"Prompt version directory and metadata label. Defaults to {DEFAULT_PROMPT_VERSION}.",
    )
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=DEFAULT_RUNS_ROOT,
        help="Root directory for model-specific runs. Defaults to experiments/humanevalx_cpp_runs.",
    )
    parser.add_argument("--problem-ids", nargs="*", default=None, help="Explicit problem IDs to process.")
    parser.add_argument("--limit", type=int, default=10, help="Number of problems to prepare/use when IDs are omitted.")
    parser.add_argument("--start-index", type=int, default=0, help="Dataset start index for prepare_dataset.py.")
    parser.add_argument("--design-temperature", type=float, default=0.0, help="Temperature for design generation.")
    parser.add_argument("--pass1-temperature", type=float, default=0.0, help="Temperature for pass@1 sample.")
    parser.add_argument("--pass3-temperature", type=float, default=0.2, help="Temperature for pass@3 samples.")
    parser.add_argument("--pass3-samples", type=int, default=3, help="Number of pass@3 samples. Defaults to 3.")
    parser.add_argument("--compiler", default="g++", help="C++ compiler command or path. Defaults to g++.")
    parser.add_argument("--std", default="c++17", help="C++ standard for generated-code tests.")
    parser.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL, help=f"Ollama base URL. Defaults to {DEFAULT_OLLAMA_URL}.")
    parser.add_argument("--ollama-timeout", type=float, default=120.0, help="Ollama request timeout in seconds.")
    parser.add_argument("--test-timeout", type=float, default=10.0, help="Compile/run timeout for run_tests.py.")
    parser.add_argument("--continue-on-error", action="store_true", help="Continue after a failed step or sample.")
    parser.add_argument("--force-run", action="store_true", help="Allow reuse of an existing run directory.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned commands without executing anything.")
    parser.add_argument("--skip-prepare", action="store_true", help="Skip prepare_dataset.py.")
    parser.add_argument("--skip-design-generation", action="store_true", help="Use existing generated_design/design.md files.")
    parser.add_argument("--validate-original", action="store_true", help="Validate original.cpp during prepare_dataset.py.")
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT_DIR / path


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT_DIR).as_posix()
    except ValueError:
        return str(path)


def sanitize_model_name(model: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", model)
    sanitized = re.sub(r"_+", "_", sanitized)
    sanitized = sanitized.strip("_")
    return sanitized or "model"


def script_command(script_name: str, *args: str) -> list[str]:
    return [sys.executable, str(SCRIPTS_DIR / script_name), *args]


def problem_ids(args: argparse.Namespace) -> list[str]:
    if args.problem_ids:
        return args.problem_ids
    return [f"problem_{index:03d}" for index in range(args.limit)]


def prepare_command(args: argparse.Namespace, run_dir: Path) -> list[str]:
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


def make_design_prompt_command(args: argparse.Namespace, run_dir: Path, problem_id: str) -> list[str]:
    return script_command(
        "make_design_prompt.py",
        "--problem-id",
        problem_id,
        "--prompt-version",
        args.prompt_version,
        "--experiment-dir",
        str(run_dir),
    )


def run_design_generation_command(args: argparse.Namespace, run_dir: Path, problem_id: str) -> list[str]:
    return script_command(
        "run_design_generation.py",
        "--problem-id",
        problem_id,
        "--model",
        args.model,
        "--temperature",
        str(args.design_temperature),
        "--ollama-url",
        args.ollama_url,
        "--ollama-timeout",
        str(args.ollama_timeout),
        "--prompt-version",
        args.prompt_version,
        "--experiment-dir",
        str(run_dir),
    )


def run_code_generation_command(args: argparse.Namespace, run_dir: Path, problem_id: str, temperature: float) -> list[str]:
    return script_command(
        "run_code_generation.py",
        "--problem-id",
        problem_id,
        "--model",
        args.model,
        "--temperature",
        str(temperature),
        "--ollama-url",
        args.ollama_url,
        "--ollama-timeout",
        str(args.ollama_timeout),
        "--prompt-version",
        args.prompt_version,
        "--experiment-dir",
        str(run_dir),
    )


def run_similarity_command(run_dir: Path, problem_id: str) -> list[str]:
    return script_command("run_similarity.py", "--problem-id", problem_id, "--experiment-dir", str(run_dir))


def run_tests_command(args: argparse.Namespace, run_dir: Path, problem_id: str) -> list[str]:
    return script_command(
        "run_tests.py",
        "--problem-id",
        problem_id,
        "--compiler",
        args.compiler,
        "--std",
        args.std,
        "--timeout",
        str(args.test_timeout),
        "--experiment-dir",
        str(run_dir),
    )


def sample_specs(args: argparse.Namespace) -> list[dict[str, Any]]:
    specs = [
        {
            "pass_name": "pass1",
            "sample_name": "sample_001",
            "sample_index": 1,
            "temperature": args.pass1_temperature,
        }
    ]
    for index in range(1, args.pass3_samples + 1):
        specs.append(
            {
                "pass_name": "pass3",
                "sample_name": f"sample_{index:03d}",
                "sample_index": index,
                "temperature": args.pass3_temperature,
            }
        )
    return specs


def print_command(label: str, command: list[str] | None) -> None:
    if command is None:
        print(f"{label}: skipped")
        return
    print(f"{label}:")
    print("  " + " ".join(command))


def execute(label: str, command: list[str]) -> bool:
    print_command(label, command)
    result = subprocess.run(command, check=False, cwd=ROOT_DIR)
    if result.returncode != 0:
        print(f"{label} failed with exit code {result.returncode}")
        return False
    return True


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def copy_if_exists(source: Path, destination: Path) -> None:
    if source.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)


def clear_transient_outputs(problem_dir: Path) -> None:
    for path in [
        problem_dir / "generated_code" / "generated.cpp",
        problem_dir / "results" / "code_generation_metadata.json",
        problem_dir / "results" / "similarity.json",
        problem_dir / "results" / "test_results.json",
    ]:
        if path.exists():
            path.unlink()


def archive_sample_outputs(run_dir: Path, problem_id: str, spec: dict[str, Any], args: argparse.Namespace) -> None:
    problem_dir = run_dir / "problems" / problem_id
    pass_name = str(spec["pass_name"])
    sample_name = str(spec["sample_name"])
    generated_source = problem_dir / "generated_code" / "generated.cpp"
    sample_code_dir = problem_dir / "generated_code" / pass_name / sample_name
    sample_results_dir = problem_dir / "results" / pass_name / sample_name

    copy_if_exists(generated_source, sample_code_dir / "generated.cpp")
    copy_if_exists(problem_dir / "results" / "code_generation_metadata.json", sample_results_dir / "code_generation_metadata.json")
    copy_if_exists(problem_dir / "results" / "similarity.json", sample_results_dir / "similarity.json")
    copy_if_exists(problem_dir / "results" / "test_results.json", sample_results_dir / "test_results.json")
    write_json(
        sample_results_dir / "sample_metadata.json",
        {
            "problem_id": problem_id,
            "model": args.model,
            "prompt_version": args.prompt_version,
            "pass_name": pass_name,
            "sample_name": sample_name,
            "sample_index": spec["sample_index"],
            "temperature": spec["temperature"],
            "generated_path": display_path(sample_code_dir / "generated.cpp"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


def run_problem(args: argparse.Namespace, run_dir: Path, problem_id: str) -> bool:
    steps: list[tuple[str, list[str]]] = [
        (f"{problem_id} make_design_prompt", make_design_prompt_command(args, run_dir, problem_id)),
    ]
    if not args.skip_design_generation:
        steps.append((f"{problem_id} run_design_generation", run_design_generation_command(args, run_dir, problem_id)))

    for label, command in steps:
        if not execute(label, command):
            return False

    problem_ok = True
    for spec in sample_specs(args):
        clear_transient_outputs(run_dir / "problems" / problem_id)
        sample_label = f"{problem_id} {spec['pass_name']} {spec['sample_name']}"
        for label, command in [
            (f"{sample_label} run_code_generation", run_code_generation_command(args, run_dir, problem_id, float(spec["temperature"]))),
            (f"{sample_label} run_similarity", run_similarity_command(run_dir, problem_id)),
            (f"{sample_label} run_tests", run_tests_command(args, run_dir, problem_id)),
        ]:
            if not execute(label, command):
                problem_ok = False
                if not args.continue_on_error:
                    return False
                break
        archive_sample_outputs(run_dir, problem_id, spec, args)
    return problem_ok


def dry_run(args: argparse.Namespace, run_dir: Path) -> int:
    print()
    print("Dry-run: no directories will be created, no files will be written, and no commands will be executed.")
    print_command("prepare_dataset", None if args.skip_prepare else prepare_command(args, run_dir))
    for problem_id in problem_ids(args):
        print(f"=== {problem_id} ===")
        print_command("make_design_prompt", make_design_prompt_command(args, run_dir, problem_id))
        print_command(
            "run_design_generation",
            None if args.skip_design_generation else run_design_generation_command(args, run_dir, problem_id),
        )
        for spec in sample_specs(args):
            sample_root = run_dir / "problems" / problem_id
            print(f"{spec['pass_name']} {spec['sample_name']} temperature={spec['temperature']}")
            print_command("run_code_generation", run_code_generation_command(args, run_dir, problem_id, float(spec["temperature"])))
            print_command("run_similarity", run_similarity_command(run_dir, problem_id))
            print_command("run_tests", run_tests_command(args, run_dir, problem_id))
            print(f"  generated archive: {display_path(sample_root / 'generated_code' / spec['pass_name'] / spec['sample_name'] / 'generated.cpp')}")
            print(f"  result archive: {display_path(sample_root / 'results' / spec['pass_name'] / spec['sample_name'])}")
    print(f"run_metadata: {display_path(run_dir / 'run_metadata.json')}")
    return 0


def run_metadata(args: argparse.Namespace, run_dir: Path, model_dir_name: str) -> dict[str, Any]:
    return {
        "model": args.model,
        "model_dir_name": model_dir_name,
        "prompt_version": args.prompt_version,
        "run_dir": display_path(run_dir),
        "problem_ids": problem_ids(args),
        "limit": args.limit,
        "start_index": args.start_index,
        "design_temperature": args.design_temperature,
        "pass1_temperature": args.pass1_temperature,
        "pass3_temperature": args.pass3_temperature,
        "pass3_samples": args.pass3_samples,
        "compiler": args.compiler,
        "std": args.std,
        "ollama_url": args.ollama_url,
        "ollama_timeout": args.ollama_timeout,
        "test_timeout": args.test_timeout,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def main() -> int:
    args = parse_args()
    runs_root = resolve_path(args.runs_root)
    model_dir_name = sanitize_model_name(args.model)
    run_dir = runs_root / args.prompt_version / model_dir_name

    print(f"model: {args.model}")
    print(f"model_dir_name: {model_dir_name}")
    print(f"run_dir: {display_path(run_dir)}")
    print(f"pass@1 temperature: {args.pass1_temperature}")
    print(f"pass@3 temperature: {args.pass3_temperature}, samples: {args.pass3_samples}")

    if args.dry_run:
        return dry_run(args, run_dir)

    if run_dir.exists() and not args.force_run:
        print("Run directory already exists:")
        print(f"  {display_path(run_dir)}")
        print("Use --force-run to overwrite/reuse it.")
        return 1

    run_dir.mkdir(parents=True, exist_ok=True)
    write_json(run_dir / "run_metadata.json", run_metadata(args, run_dir, model_dir_name))

    if not args.skip_prepare and not execute("prepare_dataset", prepare_command(args, run_dir)):
        return 1

    failed: list[str] = []
    for problem_id in problem_ids(args):
        print(f"=== {problem_id} ===")
        if not run_problem(args, run_dir, problem_id):
            failed.append(problem_id)
            if not args.continue_on_error:
                return 1

    if failed:
        print("Pass@k experiment completed with failed problems:")
        for problem_id in failed:
            print(f"- {problem_id}")
        return 1

    print("Pass@k experiment completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
