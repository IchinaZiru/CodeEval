"""Placeholder dataset preparation script for the HumanEval-X C++ pipeline.

This script intentionally does not download or import HumanEval-X yet. It only
checks that the initial dummy-problem layout exists.
"""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT_DIR = ROOT_DIR / "experiments" / "humanevalx_cpp"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check the initial dummy dataset layout without importing HumanEval-X."
    )
    parser.add_argument(
        "--experiment-dir",
        type=Path,
        default=DEFAULT_EXPERIMENT_DIR,
        help="Experiment directory. Defaults to experiments/humanevalx_cpp.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    problem_dir = args.experiment_dir / "problems" / "problem_000"
    required_paths = [
        ROOT_DIR / "data" / "raw",
        ROOT_DIR / "data" / "selected" / "selected_ids.txt",
        problem_dir / "spec.md",
        problem_dir / "original.cpp",
        problem_dir / "test.cpp",
    ]

    missing = [path for path in required_paths if not path.exists()]
    if missing:
        print("Missing required paths:")
        for path in missing:
            print(f"- {path}")
        return 1

    print("Initial dummy dataset layout is ready.")
    print("HumanEval-X import is intentionally out of scope for this stage.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
