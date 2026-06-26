"""Export original/generated C++ files for Dolos-style external comparison."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from evaluation_metrics import display_path, problem_dirs, read_json, resolve_path, write_csv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export flat C++ files and a pair manifest for Dolos.")
    parser.add_argument("--run-dir", type=Path, required=True, help="Model run directory.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory. Defaults to <run-dir>/dolos_inputs.",
    )
    return parser.parse_args()


def copy_if_exists(source: Path, destination: Path) -> bool:
    if not source.exists():
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    return True


def main() -> int:
    args = parse_args()
    run_dir = resolve_path(args.run_dir)
    output_dir = resolve_path(args.output_dir) if args.output_dir else run_dir / "dolos_inputs"

    if not run_dir.exists():
        print(f"Run directory not found: {display_path(run_dir)}")
        return 1

    rows = []
    for problem_dir in problem_dirs(run_dir):
        problem_id = problem_dir.name
        original_path = problem_dir / "original.cpp"
        generated_path = problem_dir / "generated_code" / "generated.cpp"
        original_output = output_dir / f"{problem_id}_original.cpp"
        generated_output = output_dir / f"{problem_id}_generated.cpp"
        tests = read_json(problem_dir / "results" / "test_results.json") or {}

        original_exists = copy_if_exists(original_path, original_output)
        generated_exists = copy_if_exists(generated_path, generated_output)
        rows.append(
            {
                "problem_id": problem_id,
                "original_file": original_output.name,
                "generated_file": generated_output.name,
                "original_exists": original_exists,
                "generated_exists": generated_exists,
                "test_status": tests.get("status", "missing_test_result"),
                "passed": tests.get("passed", False),
            }
        )

    if not rows:
        print(f"No problem directories found in: {display_path(run_dir / 'problems')}")
        return 1

    pairs_path = output_dir / "dolos_pairs.csv"
    write_csv(
        pairs_path,
        rows,
        ["problem_id", "original_file", "generated_file", "original_exists", "generated_exists", "test_status", "passed"],
    )
    print(f"Wrote Dolos inputs: {display_path(output_dir)}")
    print(f"Wrote Dolos pairs: {display_path(pairs_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
