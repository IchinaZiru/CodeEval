"""Compute code similarity and structural metrics for one model run."""

from __future__ import annotations

import argparse
from pathlib import Path

from evaluation_metrics import (
    CODE_METRIC_FIELDS,
    compute_code_metrics_for_problem,
    display_path,
    problem_dirs,
    resolve_path,
    write_csv,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute code metrics for HumanEval-X C++ run outputs.")
    parser.add_argument("--run-dir", type=Path, required=True, help="Model run directory.")
    parser.add_argument("--problem-id", default="problem_000", help="Problem ID to process when --all is not used.")
    parser.add_argument("--all", action="store_true", help="Process all problem_* directories in the run.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Summary output directory. Defaults to <run-dir>/summary.",
    )
    return parser.parse_args()


def selected_problem_dirs(run_dir: Path, problem_id: str, all_problems: bool) -> list[Path]:
    if all_problems:
        return problem_dirs(run_dir)
    return [run_dir / "problems" / problem_id]


def main() -> int:
    args = parse_args()
    run_dir = resolve_path(args.run_dir)
    output_dir = resolve_path(args.output_dir) if args.output_dir else run_dir / "summary"
    selected_dirs = selected_problem_dirs(run_dir, args.problem_id, args.all)

    if not run_dir.exists():
        print(f"Run directory not found: {display_path(run_dir)}")
        return 1
    if not selected_dirs:
        print(f"No problem directories found in: {display_path(run_dir / 'problems')}")
        return 1

    rows = []
    for problem_dir in selected_dirs:
        metrics = compute_code_metrics_for_problem(problem_dir)
        write_json(problem_dir / "results" / "code_metrics.json", metrics)
        rows.append(metrics)

    fields = ["problem_id", "status", "original_exists", "generated_exists", *CODE_METRIC_FIELDS]
    write_csv(output_dir / "code_metrics_summary.csv", rows, fields)

    print(f"Wrote code metrics for {len(rows)} problems.")
    print(f"Wrote summary: {display_path(output_dir / 'code_metrics_summary.csv')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
