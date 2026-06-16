"""Summarize model-specific HumanEval-X C++ runs into CSV files."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_RUNS_ROOT = ROOT_DIR / "experiments" / "humanevalx_cpp_runs"
DEFAULT_PROMPT_VERSION = "prompt_v1_baseline"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize model run success rates and similarity scores for one prompt version."
    )
    parser.add_argument(
        "--prompt-version",
        default=DEFAULT_PROMPT_VERSION,
        help=f"Prompt version directory. Defaults to {DEFAULT_PROMPT_VERSION}.",
    )
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=DEFAULT_RUNS_ROOT,
        help="Root directory for model-specific runs. Defaults to experiments/humanevalx_cpp_runs.",
    )
    parser.add_argument(
        "--models",
        nargs="*",
        default=None,
        help="Optional model directory names to include. Defaults to all directories under the prompt version.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory. Defaults to <runs-root>/<prompt-version>/summary.",
    )
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT_DIR / path


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT_DIR).as_posix()
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def model_dirs(prompt_dir: Path, requested_models: list[str] | None) -> list[Path]:
    if requested_models:
        return [prompt_dir / model for model in requested_models]
    return sorted(path for path in prompt_dir.iterdir() if path.is_dir() and path.name != "summary")


def metadata_task_id(problem_dir: Path) -> str:
    metadata = read_json(problem_dir / "metadata.json") or {}
    return str(metadata.get("task_id", ""))


def run_model_name(model_dir: Path) -> str:
    metadata = read_json(model_dir / "run_metadata.json") or {}
    return str(metadata.get("model") or model_dir.name)


def problem_row(prompt_version: str, model_dir: Path, problem_dir: Path) -> dict[str, Any]:
    similarity = read_json(problem_dir / "results" / "similarity.json")
    tests = read_json(problem_dir / "results" / "test_results.json")
    original_validation = read_json(problem_dir / "results" / "original_validation.json")
    design_path = problem_dir / "generated_design" / "design.md"
    code_path = problem_dir / "generated_code" / "generated.cpp"

    similarity_status = similarity.get("status") if similarity else "missing_similarity_result"
    test_status = tests.get("status") if tests else "missing_test_result"

    return {
        "prompt_version": prompt_version,
        "model_dir": model_dir.name,
        "model": run_model_name(model_dir),
        "problem_id": problem_dir.name,
        "task_id": metadata_task_id(problem_dir),
        "design_generated": design_path.exists(),
        "code_generated": code_path.exists(),
        "similarity_status": similarity_status,
        "similarity": similarity.get("similarity") if similarity else "",
        "test_status": test_status,
        "passed": tests.get("passed") if tests else "",
        "compile_returncode": tests.get("compile_returncode") if tests else "",
        "run_returncode": tests.get("run_returncode") if tests else "",
        "original_validation_status": original_validation.get("status") if original_validation else "",
    }


def collect_problem_rows(prompt_version: str, model_dir: Path) -> list[dict[str, Any]]:
    problems_dir = model_dir / "problems"
    if not problems_dir.exists():
        return []
    return [
        problem_row(prompt_version, model_dir, problem_dir)
        for problem_dir in sorted(path for path in problems_dir.glob("problem_*") if path.is_dir())
    ]


def numeric_similarity_values(rows: list[dict[str, Any]]) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = row.get("similarity")
        if isinstance(value, (int, float)):
            values.append(float(value))
    return values


def model_summary_row(prompt_version: str, model_dir: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    similarity_values = numeric_similarity_values(rows)
    tests_passed = sum(1 for row in rows if row.get("passed") is True)
    failed_problem_ids = [
        str(row["problem_id"])
        for row in rows
        if row.get("passed") is not True
    ]

    return {
        "prompt_version": prompt_version,
        "model_dir": model_dir.name,
        "model": run_model_name(model_dir),
        "total_problems": total,
        "design_generated_count": sum(1 for row in rows if row.get("design_generated") is True),
        "code_generated_count": sum(1 for row in rows if row.get("code_generated") is True),
        "similarity_available_count": len(similarity_values),
        "average_similarity": (sum(similarity_values) / len(similarity_values)) if similarity_values else "",
        "compile_success_count": sum(1 for row in rows if row.get("compile_returncode") == 0),
        "tests_passed_count": tests_passed,
        "success_rate": (tests_passed / total) if total else "",
        "pass_at_1": (tests_passed / total) if total else "",
        "failed_problem_ids": ";".join(failed_problem_ids),
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def main() -> int:
    args = parse_args()
    runs_root = resolve_path(args.runs_root)
    prompt_dir = runs_root / args.prompt_version
    output_dir = resolve_path(args.output_dir) if args.output_dir else prompt_dir / "summary"

    if not prompt_dir.exists():
        print(f"Prompt version directory not found: {display_path(prompt_dir)}")
        return 1

    all_problem_rows: list[dict[str, Any]] = []
    model_summary_rows: list[dict[str, Any]] = []

    for model_dir in model_dirs(prompt_dir, args.models):
        if not model_dir.exists():
            print(f"Model directory not found: {display_path(model_dir)}")
            return 1
        rows = collect_problem_rows(args.prompt_version, model_dir)
        all_problem_rows.extend(rows)
        model_summary_rows.append(model_summary_row(args.prompt_version, model_dir, rows))

    model_summary_fields = [
        "prompt_version",
        "model_dir",
        "model",
        "total_problems",
        "design_generated_count",
        "code_generated_count",
        "similarity_available_count",
        "average_similarity",
        "compile_success_count",
        "tests_passed_count",
        "success_rate",
        "pass_at_1",
        "failed_problem_ids",
    ]
    problem_result_fields = [
        "prompt_version",
        "model_dir",
        "model",
        "problem_id",
        "task_id",
        "design_generated",
        "code_generated",
        "similarity_status",
        "similarity",
        "test_status",
        "passed",
        "compile_returncode",
        "run_returncode",
        "original_validation_status",
    ]

    model_summary_path = output_dir / "model_summary.csv"
    problem_results_path = output_dir / "problem_results.csv"
    write_csv(model_summary_path, model_summary_rows, model_summary_fields)
    write_csv(problem_results_path, all_problem_rows, problem_result_fields)

    print(f"Wrote model summary: {display_path(model_summary_path)}")
    print(f"Wrote problem results: {display_path(problem_results_path)}")
    print(f"Models summarized: {len(model_summary_rows)}")
    print(f"Problem rows summarized: {len(all_problem_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
