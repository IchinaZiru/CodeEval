"""Summarize pass@1/pass@3 sample results for one model run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from evaluation_metrics import display_path, problem_dirs, read_json, resolve_path, write_csv, write_json


PASSK_FIELDS = [
    "problem_id",
    "pass1_temp0.0",
    "pass1_status",
    "pass1_passed_samples",
    "pass1_total_samples",
    "pass3_temp0.2",
    "pass3_statuses",
    "pass3_passed_samples",
    "pass3_total_samples",
    "best_status",
    "failure_reasons",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize pass@k sample outputs for one run.")
    parser.add_argument("--run-dir", type=Path, required=True, help="Model run directory.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory. Defaults to <run-dir>/summary.",
    )
    return parser.parse_args()


def sample_result_paths(problem_dir: Path, pass_name: str) -> list[Path]:
    root = problem_dir / "results" / pass_name
    if not root.exists():
        return []
    return sorted(root.glob("sample_*/test_results.json"))


def sample_rows(problem_dir: Path, pass_name: str) -> list[dict[str, Any]]:
    rows = []
    for path in sample_result_paths(problem_dir, pass_name):
        payload = read_json(path) or {}
        rows.append(
            {
                "sample_name": path.parent.name,
                "status": payload.get("status", "missing_test_result"),
                "passed": payload.get("passed") is True,
                "reason": payload.get("reason", ""),
            }
        )
    return rows


def status_summary(rows: list[dict[str, Any]]) -> str:
    return ";".join(f"{row['sample_name']}:{row['status']}" for row in rows)


def failure_reasons(pass1_rows: list[dict[str, Any]], pass3_rows: list[dict[str, Any]]) -> str:
    reasons = []
    for row in [*pass1_rows, *pass3_rows]:
        if row.get("passed") is True:
            continue
        reason = row.get("reason") or row.get("status") or "failed"
        reasons.append(f"{row.get('sample_name')}:{reason}")
    return ";".join(reasons)


def problem_summary(problem_dir: Path) -> dict[str, Any]:
    pass1_rows = sample_rows(problem_dir, "pass1")
    pass3_rows = sample_rows(problem_dir, "pass3")
    pass1_passed = sum(1 for row in pass1_rows if row["passed"])
    pass3_passed = sum(1 for row in pass3_rows if row["passed"])
    pass1_success = pass1_passed > 0
    pass3_success = pass3_passed > 0
    return {
        "problem_id": problem_dir.name,
        "pass1_temp0.0": pass1_success,
        "pass1_status": status_summary(pass1_rows),
        "pass1_passed_samples": pass1_passed,
        "pass1_total_samples": len(pass1_rows),
        "pass3_temp0.2": pass3_success,
        "pass3_statuses": status_summary(pass3_rows),
        "pass3_passed_samples": pass3_passed,
        "pass3_total_samples": len(pass3_rows),
        "best_status": "passed" if pass1_success or pass3_success else "failed",
        "failure_reasons": failure_reasons(pass1_rows, pass3_rows),
    }


def rate(count: int, total: int) -> float | None:
    if total == 0:
        return None
    return count / total


def metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    pass1_count = sum(1 for row in rows if row["pass1_temp0.0"] is True)
    pass3_count = sum(1 for row in rows if row["pass3_temp0.2"] is True)
    return {
        "total_problems": total,
        "pass@1_temp0.0_count": pass1_count,
        "pass@1_temp0.0_rate": rate(pass1_count, total),
        "pass@3_temp0.2_count": pass3_count,
        "pass@3_temp0.2_rate": rate(pass3_count, total),
        "pass3_total_samples_per_problem": max((row["pass3_total_samples"] for row in rows), default=0),
    }


def main() -> int:
    args = parse_args()
    run_dir = resolve_path(args.run_dir)
    output_dir = resolve_path(args.output_dir) if args.output_dir else run_dir / "summary"

    if not run_dir.exists():
        print(f"Run directory not found: {display_path(run_dir)}")
        return 1

    rows = [problem_summary(problem_dir) for problem_dir in problem_dirs(run_dir)]
    if not rows:
        print(f"No problem directories found in: {display_path(run_dir / 'problems')}")
        return 1

    summary_path = output_dir / "passk_summary.csv"
    metrics_path = output_dir / "passk_metrics.json"
    write_csv(summary_path, rows, PASSK_FIELDS)
    write_json(metrics_path, metrics(rows))

    print(f"Wrote pass@k summary: {display_path(summary_path)}")
    print(f"Wrote pass@k metrics: {display_path(metrics_path)}")
    print(json.dumps(metrics(rows), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
