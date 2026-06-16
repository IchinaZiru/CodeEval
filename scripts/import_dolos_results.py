"""Merge external Dolos-style CSV results into combined_summary.csv."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from evaluation_metrics import display_path, read_csv_rows, resolve_path, run_summary_metrics, write_csv, write_json


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


PROBLEM_FILE_RE = re.compile(r"^(problem_\d+)_(original|generated)\.cpp$")


def problem_file_role(path_text: str) -> tuple[str, str] | None:
    filename = Path(path_text).name
    match = PROBLEM_FILE_RE.match(filename)
    if not match:
        return None
    return match.group(1), match.group(2)


def parse_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_generic_dolos_rows(rows: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    parsed: dict[str, dict[str, Any]] = {}
    for row in rows:
        problem_id = row.get("problem_id", "").strip()
        if not problem_id:
            continue
        parsed[problem_id] = {
            "dolos_similarity": row.get("dolos_similarity", ""),
            "dolos_notes": row.get("dolos_notes", ""),
        }
    return parsed


def parse_dolos_pairs_rows(rows: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    parsed: dict[str, dict[str, Any]] = {}
    for row in rows:
        left = problem_file_role(row.get("leftFilePath", ""))
        right = problem_file_role(row.get("rightFilePath", ""))
        if left is None or right is None:
            continue

        left_problem_id, left_role = left
        right_problem_id, right_role = right
        if left_problem_id != right_problem_id:
            continue
        if {left_role, right_role} != {"original", "generated"}:
            continue

        similarity = parse_float(row.get("similarity"))
        if similarity is None:
            continue

        current = parsed.get(left_problem_id)
        if current is None or similarity > float(current["dolos_similarity"]):
            parsed[left_problem_id] = {
                "dolos_similarity": similarity,
                "dolos_notes": f"dolos_pairs.csv row id={row.get('id', '')}".strip(),
            }
    return parsed


def load_dolos_results(path: Path) -> dict[str, dict[str, Any]]:
    rows = read_csv_rows(path)
    if not rows:
        return {}
    fieldnames = set(rows[0].keys())
    if {"problem_id", "dolos_similarity"}.issubset(fieldnames):
        return parse_generic_dolos_rows(rows)
    if {"leftFilePath", "rightFilePath", "similarity"}.issubset(fieldnames):
        return parse_dolos_pairs_rows(rows)
    raise ValueError(
        "Unsupported Dolos CSV format. Expected either "
        "problem_id,dolos_similarity,dolos_notes or Dolos pairs.csv with "
        "leftFilePath,rightFilePath,similarity."
    )


def coerce_numeric_for_metrics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    converted: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        if item.get("passed") == "True":
            item["passed"] = True
        elif item.get("passed") == "False":
            item["passed"] = False
        for key, value in list(item.items()):
            if key in {"problem_id", "task_id", "status", "reason", "dolos_notes", "generated_path", "test_path"}:
                continue
            if isinstance(value, str) and value.strip():
                number = parse_float(value)
                if number is not None:
                    item[key] = number
        converted.append(item)
    return converted


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
    try:
        dolos_by_problem = load_dolos_results(dolos_results_path)
    except ValueError as exc:
        print(exc)
        return 1

    fieldnames = list(combined_rows[0].keys()) if combined_rows else ["problem_id"]
    for field in ["dolos_similarity", "dolos_notes"]:
        if field not in fieldnames:
            fieldnames.append(field)

    for row in combined_rows:
        dolos = dolos_by_problem.get(row.get("problem_id", ""), {})
        row["dolos_similarity"] = dolos.get("dolos_similarity", row.get("dolos_similarity", ""))
        row["dolos_notes"] = dolos.get("dolos_notes", row.get("dolos_notes", ""))

    write_csv(output_path, combined_rows, fieldnames)
    metrics = run_summary_metrics(coerce_numeric_for_metrics(combined_rows))
    write_json(run_dir / "summary" / "summary_metrics_with_dolos.json", metrics)
    print(f"Wrote combined summary with Dolos results: {display_path(output_path)}")
    print(f"Wrote summary metrics with Dolos results: {display_path(run_dir / 'summary' / 'summary_metrics_with_dolos.json')}")
    print(f"Imported Dolos similarities: {len(dolos_by_problem)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
