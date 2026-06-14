"""Aggregate per-problem result JSON files into experiment summary files."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT_DIR = ROOT_DIR / "experiments" / "humanevalx_cpp"


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT_DIR).as_posix()
    except ValueError:
        return str(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize similarity and test results across problems."
    )
    parser.add_argument(
        "--experiment-dir",
        type=Path,
        default=DEFAULT_EXPERIMENT_DIR,
        help="Experiment directory. Defaults to experiments/humanevalx_cpp.",
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_similarity_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = ["problem_id", "status", "similarity", "original_path", "generated_path"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_test_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = ["problem_id", "status", "passed", "compiler", "compile_returncode", "run_returncode"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def compute_metrics(problem_rows: list[dict[str, Any]]) -> dict[str, Any]:
    total_problems = len(problem_rows)
    similarity_values = [
        row["similarity"]
        for row in problem_rows
        if isinstance(row.get("similarity"), (int, float))
    ]
    tests_passed_count = sum(1 for row in problem_rows if row.get("test_passed") is True)
    failed_problem_ids = [
        row["problem_id"]
        for row in problem_rows
        if not (
            row.get("design_generated")
            and row.get("code_generated")
            and row.get("similarity_available")
            and row.get("test_passed") is True
        )
    ]

    return {
        "total_problems": total_problems,
        "design_generated_count": sum(1 for row in problem_rows if row.get("design_generated")),
        "code_generated_count": sum(1 for row in problem_rows if row.get("code_generated")),
        "similarity_available_count": len(similarity_values),
        "average_similarity": (sum(similarity_values) / len(similarity_values)) if similarity_values else None,
        "compile_success_count": sum(1 for row in problem_rows if row.get("compile_returncode") == 0),
        "tests_passed_count": tests_passed_count,
        "pass_at_1": (tests_passed_count / total_problems) if total_problems else 0.0,
        "failed_problem_ids": failed_problem_ids,
    }


def write_report(path: Path, metrics: dict[str, Any]) -> None:
    average_similarity = metrics["average_similarity"]
    average_similarity_text = f"{average_similarity:.6f}" if average_similarity is not None else "N/A"
    failed_problem_ids = metrics["failed_problem_ids"]

    lines = [
        "# HumanEval-X C++ Dummy Experiment Report",
        "",
        f"- total_problems: {metrics['total_problems']}",
        f"- design_generated_count: {metrics['design_generated_count']}",
        f"- code_generated_count: {metrics['code_generated_count']}",
        f"- similarity_available_count: {metrics['similarity_available_count']}",
        f"- average_similarity: {average_similarity_text}",
        f"- compile_success_count: {metrics['compile_success_count']}",
        f"- tests_passed_count: {metrics['tests_passed_count']}",
        f"- pass_at_1: {metrics['pass_at_1']:.6f}",
        f"- failed_problem_ids: {', '.join(failed_problem_ids) if failed_problem_ids else 'None'}",
        "",
        "This report is generated from per-problem JSON files under `results/`.",
        "The current stage uses the dummy `problem_000` through `problem_004` pipeline.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    problems_dir = args.experiment_dir / "problems"
    summary_dir = args.experiment_dir / "summary"
    summary_dir.mkdir(parents=True, exist_ok=True)

    similarity_rows: list[dict[str, Any]] = []
    test_rows: list[dict[str, Any]] = []
    problem_rows: list[dict[str, Any]] = []

    for problem_dir in sorted(path for path in problems_dir.glob("problem_*") if path.is_dir()):
        problem_id = problem_dir.name
        similarity = read_json(problem_dir / "results" / "similarity.json")
        tests = read_json(problem_dir / "results" / "test_results.json")
        design_path = problem_dir / "generated_design" / "design.md"
        code_path = problem_dir / "generated_code" / "generated.cpp"

        similarity_rows.append(
            similarity
            or {
                "problem_id": problem_id,
                "status": "missing_similarity_result",
                "similarity": "",
                "original_path": display_path(problem_dir / "original.cpp"),
                "generated_path": display_path(problem_dir / "generated_code" / "generated.cpp"),
            }
        )
        test_rows.append(
            tests
            or {
                "problem_id": problem_id,
                "status": "missing_test_result",
                "passed": "",
                "compiler": "",
                "compile_returncode": "",
                "run_returncode": "",
            }
        )

        similarity_available = bool(similarity and similarity.get("status") == "success")
        similarity_value = similarity.get("similarity") if similarity_available else None
        problem_rows.append(
            {
                "problem_id": problem_id,
                "design_generated": design_path.exists(),
                "code_generated": code_path.exists(),
                "similarity_available": similarity_available,
                "similarity": similarity_value,
                "compile_returncode": tests.get("compile_returncode") if tests else None,
                "test_status": tests.get("status") if tests else "missing_test_result",
                "test_passed": tests.get("passed") if tests else False,
            }
        )

    write_similarity_csv(summary_dir / "similarity_results.csv", similarity_rows)
    write_test_csv(summary_dir / "test_results.csv", test_rows)
    metrics = compute_metrics(problem_rows)
    write_json(summary_dir / "summary_metrics.json", metrics)
    write_report(summary_dir / "report.md", metrics)

    print(f"Wrote summary files under: {summary_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
