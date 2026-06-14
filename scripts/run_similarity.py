"""Compute a simple text similarity score between original and generated C++."""

from __future__ import annotations

import argparse
import json
from difflib import SequenceMatcher
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
        description="Compare original.cpp and generated_code/generated.cpp."
    )
    parser.add_argument("--problem-id", default="problem_000", help="Problem ID to process.")
    parser.add_argument(
        "--experiment-dir",
        type=Path,
        default=DEFAULT_EXPERIMENT_DIR,
        help="Experiment directory. Defaults to experiments/humanevalx_cpp.",
    )
    return parser.parse_args()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    problem_dir = args.experiment_dir / "problems" / args.problem_id
    original_path = problem_dir / "original.cpp"
    generated_path = problem_dir / "generated_code" / "generated.cpp"
    result_path = problem_dir / "results" / "similarity.json"

    if not original_path.exists():
        write_json(
            result_path,
            {
                "problem_id": args.problem_id,
                "status": "missing_original",
                "similarity": None,
                "original_path": display_path(original_path),
                "generated_path": display_path(generated_path),
            },
        )
        print(f"Original source not found: {original_path}")
        return 1

    if not generated_path.exists():
        write_json(
            result_path,
            {
                "problem_id": args.problem_id,
                "status": "missing_generated_code",
                "similarity": None,
                "original_path": display_path(original_path),
                "generated_path": display_path(generated_path),
            },
        )
        print(f"Generated source not found: {generated_path}")
        return 1

    original_text = original_path.read_text(encoding="utf-8")
    generated_text = generated_path.read_text(encoding="utf-8")
    similarity = SequenceMatcher(None, original_text, generated_text).ratio()

    write_json(
        result_path,
        {
            "problem_id": args.problem_id,
            "status": "success",
            "similarity": similarity,
            "original_path": display_path(original_path),
            "generated_path": display_path(generated_path),
            "original_chars": len(original_text),
            "generated_chars": len(generated_text),
        },
    )
    print(f"Wrote similarity result: {result_path}")
    print(f"Similarity: {similarity:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
