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


def write_report(path: Path, similarity_rows: list[dict[str, Any]], test_rows: list[dict[str, Any]]) -> None:
    completed_similarity = [row for row in similarity_rows if row.get("status") == "success"]
    completed_tests = [row for row in test_rows if row.get("passed") is True]
    total_problems = max(len(similarity_rows), len(test_rows))

    lines = [
        "# HumanEval-X C++ Dummy Experiment Report",
        "",
        f"- Problems summarized: {total_problems}",
        f"- Similarity results available: {len(completed_similarity)}",
        f"- Tests passed: {len(completed_tests)}",
        "",
        "This report is generated from per-problem JSON files under `results/`.",
        "The current stage uses only the dummy `problem_000` pipeline.",
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

    for problem_dir in sorted(path for path in problems_dir.glob("problem_*") if path.is_dir()):
        problem_id = problem_dir.name
        similarity = read_json(problem_dir / "results" / "similarity.json")
        tests = read_json(problem_dir / "results" / "test_results.json")

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

    write_similarity_csv(summary_dir / "similarity_results.csv", similarity_rows)
    write_test_csv(summary_dir / "test_results.csv", test_rows)
    write_report(summary_dir / "report.md", similarity_rows, test_rows)

    print(f"Wrote summary files under: {summary_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
