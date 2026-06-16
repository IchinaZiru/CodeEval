"""Summarize one model-specific HumanEval-X C++ run."""

from __future__ import annotations

import argparse
from pathlib import Path

from evaluation_metrics import (
    COMBINED_SUMMARY_FIELDS,
    TEST_SUMMARY_FIELDS,
    collect_run_rows,
    display_path,
    resolve_path,
    run_summary_metrics,
    write_csv,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize test, code, and design metrics for one model run.")
    parser.add_argument("--run-dir", type=Path, required=True, help="Model run directory.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory. Defaults to <run-dir>/summary.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_dir = resolve_path(args.run_dir)
    output_dir = resolve_path(args.output_dir) if args.output_dir else run_dir / "summary"

    if not run_dir.exists():
        print(f"Run directory not found: {display_path(run_dir)}")
        return 1

    test_rows, combined_rows = collect_run_rows(run_dir)
    if not combined_rows:
        print(f"No problem directories found in: {display_path(run_dir / 'problems')}")
        return 1

    metrics = run_summary_metrics(combined_rows)
    write_csv(output_dir / "test_summary.csv", test_rows, TEST_SUMMARY_FIELDS)
    write_csv(output_dir / "combined_summary.csv", combined_rows, COMBINED_SUMMARY_FIELDS)
    write_json(output_dir / "summary_metrics.json", metrics)

    print(f"Wrote test summary: {display_path(output_dir / 'test_summary.csv')}")
    print(f"Wrote combined summary: {display_path(output_dir / 'combined_summary.csv')}")
    print(f"Wrote summary metrics: {display_path(output_dir / 'summary_metrics.json')}")
    print(f"total={metrics['total']} passed={metrics['passed']} pass_rate={metrics['pass_rate']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
