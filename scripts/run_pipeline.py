"""Run the dummy HumanEval-X C++ regeneration pipeline for multiple problems."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from ollama_client import DEFAULT_OLLAMA_URL


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"
DEFAULT_EXPERIMENT_DIR = ROOT_DIR / "experiments" / "humanevalx_cpp"
DEFAULT_SELECTED_IDS_PATH = ROOT_DIR / "data" / "selected" / "selected_ids.txt"
DEFAULT_PROMPT_VERSION = "prompt_v2_signature_include"


@dataclass(frozen=True)
class PipelineStep:
    name: str
    command: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run prompt generation, Ollama generation, similarity, and tests for multiple problems."
    )
    parser.add_argument(
        "--problem-ids",
        nargs="*",
        default=None,
        help="Problem IDs to process. Defaults to data/selected/selected_ids.txt, then all problem_* dirs.",
    )
    parser.add_argument("--model", required=True, help="Ollama model name, for example qwen2.5-coder:7b.")
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Ollama generation temperature. Defaults to 0.",
    )
    parser.add_argument(
        "--compiler",
        default="g++",
        help="C++ compiler command or path. Defaults to g++.",
    )
    parser.add_argument(
        "--ollama-url",
        default=DEFAULT_OLLAMA_URL,
        help=f"Ollama base URL. Defaults to {DEFAULT_OLLAMA_URL}.",
    )
    parser.add_argument(
        "--ollama-timeout",
        type=float,
        default=120.0,
        help="Ollama request timeout in seconds. Defaults to 120.",
    )
    parser.add_argument(
        "--prompt-version",
        default=DEFAULT_PROMPT_VERSION,
        help=f"Prompt version label passed to generation metadata. Defaults to {DEFAULT_PROMPT_VERSION}.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue with later problems when a step fails.",
    )
    parser.add_argument(
        "--experiment-dir",
        type=Path,
        default=DEFAULT_EXPERIMENT_DIR,
        help="Experiment directory. Defaults to experiments/humanevalx_cpp.",
    )
    return parser.parse_args()


def load_default_problem_ids(experiment_dir: Path) -> list[str]:
    if DEFAULT_SELECTED_IDS_PATH.exists():
        ids = [
            line.strip()
            for line in DEFAULT_SELECTED_IDS_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        if ids:
            return ids

    problems_dir = experiment_dir / "problems"
    return sorted(path.name for path in problems_dir.glob("problem_*") if path.is_dir())


def script_command(script_name: str, *args: str) -> list[str]:
    return [sys.executable, str(SCRIPTS_DIR / script_name), *args]


def steps_for_problem(args: argparse.Namespace, problem_id: str) -> list[PipelineStep]:
    experiment_dir = str(args.experiment_dir)
    temperature = str(args.temperature)
    ollama_timeout = str(args.ollama_timeout)

    return [
        PipelineStep(
            "make_design_prompt",
            script_command(
                "make_design_prompt.py",
                "--problem-id",
                problem_id,
                "--prompt-version",
                args.prompt_version,
                "--experiment-dir",
                experiment_dir,
            ),
        ),
        PipelineStep(
            "run_design_generation",
            script_command(
                "run_design_generation.py",
                "--problem-id",
                problem_id,
                "--model",
                args.model,
                "--temperature",
                temperature,
                "--ollama-url",
                args.ollama_url,
                "--ollama-timeout",
                ollama_timeout,
                "--prompt-version",
                args.prompt_version,
                "--experiment-dir",
                experiment_dir,
            ),
        ),
        PipelineStep(
            "run_code_generation",
            script_command(
                "run_code_generation.py",
                "--problem-id",
                problem_id,
                "--model",
                args.model,
                "--temperature",
                temperature,
                "--ollama-url",
                args.ollama_url,
                "--ollama-timeout",
                ollama_timeout,
                "--prompt-version",
                args.prompt_version,
                "--experiment-dir",
                experiment_dir,
            ),
        ),
        PipelineStep(
            "run_similarity",
            script_command(
                "run_similarity.py",
                "--problem-id",
                problem_id,
                "--experiment-dir",
                experiment_dir,
            ),
        ),
        PipelineStep(
            "run_tests",
            script_command(
                "run_tests.py",
                "--problem-id",
                problem_id,
                "--compiler",
                args.compiler,
                "--experiment-dir",
                experiment_dir,
            ),
        ),
    ]


def run_step(problem_id: str, step: PipelineStep) -> bool:
    print(f"[{problem_id}] {step.name}")
    print(" ".join(step.command))
    result = subprocess.run(step.command, check=False, cwd=ROOT_DIR)
    if result.returncode != 0:
        print(f"[{problem_id}] {step.name} failed with exit code {result.returncode}")
        return False
    return True


def main() -> int:
    args = parse_args()
    args.experiment_dir = args.experiment_dir.resolve()
    problem_ids = args.problem_ids if args.problem_ids else load_default_problem_ids(args.experiment_dir)

    if not problem_ids:
        print("No problem IDs found.")
        return 1

    failed_problem_ids: list[str] = []

    for problem_id in problem_ids:
        print(f"=== {problem_id} ===")
        problem_failed = False
        for step in steps_for_problem(args, problem_id):
            if not run_step(problem_id, step):
                problem_failed = True
                failed_problem_ids.append(problem_id)
                if not args.continue_on_error:
                    print("Stopping because --continue-on-error was not specified.")
                    return 1
                break

        if problem_failed and args.continue_on_error:
            print(f"[{problem_id}] skipped remaining steps and continued.")

    if failed_problem_ids:
        print("Pipeline completed with failed problems:")
        for problem_id in failed_problem_ids:
            print(f"- {problem_id}")
        return 1

    print("Pipeline completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
