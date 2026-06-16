"""Merge external Dolos-style CSV results into combined_summary.csv."""

from __future__ import annotations

import argparse
from pathlib import Path

from evaluation_metrics import display_path, read_csv_rows, resolve_path, write_csv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import Dolos result CSV into a run combined summary.")
    parser.add_argument("--run-dir", type=Path, required=True, help="Model run directory.")
    parser.add_argument("--dolos-results", type=Path, required=True, help="CSV with problem_id,dolos_similarity,dolos_notes.")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output CSV. Defaults to <run-dir>/summary/combined_summary_with_dolos.csv.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_dir = resolve_path(args.run_dir)
    dolos_results_path = resolve_path(args.dolos_results)
    combined_path = run_dir / "summary" / "combined_summary.csv"
    output_path = resolve_path(args.output) if args.output else run_dir / "summary" / "combined_summary_with_dolos.csv"

    if not combined_path.exists():
        print(f"Combined summary not found: {display_path(combined_path)}")
        print("Run summarize_run_results.py first.")
        return 1
    if not dolos_results_path.exists():
        print(f"Dolos results CSV not found: {display_path(dolos_results_path)}")
        return 1

    combined_rows = read_csv_rows(combined_path)
    dolos_rows = read_csv_rows(dolos_results_path)
    dolos_by_problem = {row.get("problem_id", ""): row for row in dolos_rows}

    fieldnames = list(combined_rows[0].keys()) if combined_rows else ["problem_id"]
    for field in ["dolos_similarity", "dolos_notes"]:
        if field not in fieldnames:
            fieldnames.append(field)

    for row in combined_rows:
        dolos = dolos_by_problem.get(row.get("problem_id", ""), {})
        row["dolos_similarity"] = dolos.get("dolos_similarity", row.get("dolos_similarity", ""))
        row["dolos_notes"] = dolos.get("dolos_notes", row.get("dolos_notes", ""))

    write_csv(output_path, combined_rows, fieldnames)
    print(f"Wrote combined summary with Dolos results: {display_path(output_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
