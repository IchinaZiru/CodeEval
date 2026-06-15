"""Load and select HumanEval-X C++ records without materializing problem files.

Step 1 intentionally performs no writes. It only validates the local JSONL and
prints the CodeEval problem_id to HumanEval-X task_id mapping.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_RAW_JSONL = ROOT_DIR / "data" / "raw" / "humanevalx_cpp" / "humaneval_cpp.jsonl"
DEFAULT_EXPERIMENT_DIR = ROOT_DIR / "experiments" / "humanevalx_cpp"
DEFAULT_SELECTED_IDS_PATH = ROOT_DIR / "data" / "selected" / "selected_ids.txt"
REQUIRED_FIELDS = [
    "task_id",
    "prompt",
    "declaration",
    "canonical_solution",
    "test",
    "example_test",
]


class DatasetPreparationError(RuntimeError):
    """Raised when the local HumanEval-X JSONL cannot be used."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate and select HumanEval-X C++ JSONL records without writing problem files."
    )
    parser.add_argument(
        "--raw-jsonl",
        type=Path,
        default=DEFAULT_RAW_JSONL,
        help="Path to HumanEval-X C++ JSONL. Defaults to data/raw/humanevalx_cpp/humaneval_cpp.jsonl.",
    )
    parser.add_argument(
        "--experiment-dir",
        type=Path,
        default=DEFAULT_EXPERIMENT_DIR,
        help="Experiment directory. Defaults to experiments/humanevalx_cpp.",
    )
    parser.add_argument(
        "--selected-ids-path",
        type=Path,
        default=DEFAULT_SELECTED_IDS_PATH,
        help="Future selected problem ID output path. Defaults to data/selected/selected_ids.txt.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of records to select when --task-ids is not specified. Defaults to 10.",
    )
    parser.add_argument(
        "--start-index",
        type=int,
        default=0,
        help="Start index for selection when --task-ids is not specified. Defaults to 0.",
    )
    parser.add_argument(
        "--task-ids",
        nargs="+",
        default=None,
        help="Specific HumanEval-X task_id values to select. Output order follows this list.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print selected mapping without writing files.",
    )
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT_DIR).as_posix()
    except ValueError:
        return str(path)


def resolve_input_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT_DIR / path


def validate_args(limit: int, start_index: int) -> None:
    if limit < 0:
        raise DatasetPreparationError("--limit must be greater than or equal to 0.")
    if start_index < 0:
        raise DatasetPreparationError("--start-index must be greater than or equal to 0.")


def validate_record(record: dict[str, Any], line_number: int) -> None:
    missing = [field for field in REQUIRED_FIELDS if field not in record]
    if missing:
        missing_text = ", ".join(missing)
        raise DatasetPreparationError(
            f"Line {line_number} is missing required field(s): {missing_text}"
        )


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise DatasetPreparationError(
            "HumanEval-X C++ JSONL was not found:\n"
            f"  {display_path(path)}\n\n"
            "Please check --raw-jsonl or place the dataset JSONL first."
        )

    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue

            try:
                parsed = json.loads(line)
            except json.JSONDecodeError as exc:
                raise DatasetPreparationError(
                    f"Line {line_number} is not valid JSON: {exc.msg}"
                ) from exc

            if not isinstance(parsed, dict):
                raise DatasetPreparationError(f"Line {line_number} must be a JSON object.")

            validate_record(parsed, line_number)
            records.append(parsed)

    return records


def select_records(
    records: list[dict[str, Any]],
    *,
    task_ids: list[str] | None,
    start_index: int,
    limit: int,
) -> list[dict[str, Any]]:
    if task_ids:
        records_by_task_id = {str(record["task_id"]): record for record in records}
        missing = [task_id for task_id in task_ids if task_id not in records_by_task_id]
        if missing:
            missing_text = ", ".join(missing)
            raise DatasetPreparationError(f"Requested task_id(s) were not found: {missing_text}")
        return [records_by_task_id[task_id] for task_id in task_ids]

    return records[start_index : start_index + limit]


def codeeval_problem_id(index: int) -> str:
    return f"problem_{index:03d}"


def print_selection(raw_jsonl: Path, selected_records: list[dict[str, Any]]) -> None:
    print(f"Selected {len(selected_records)} problems from {display_path(raw_jsonl)}")
    print()
    for index, record in enumerate(selected_records):
        print(f"{codeeval_problem_id(index)} <- {record['task_id']}")


def main() -> int:
    args = parse_args()

    try:
        validate_args(args.limit, args.start_index)
        raw_jsonl = resolve_input_path(args.raw_jsonl)
        records = load_jsonl(raw_jsonl)
        selected_records = select_records(
            records,
            task_ids=args.task_ids,
            start_index=args.start_index,
            limit=args.limit,
        )
    except DatasetPreparationError as exc:
        print(exc)
        return 1

    print_selection(raw_jsonl, selected_records)

    if args.dry_run:
        return 0

    print()
    print(
        "dataset loading and selection succeeded, but materialization is not implemented in this step"
    )
    print(f"future experiment_dir: {display_path(resolve_input_path(args.experiment_dir))}")
    print(f"future selected_ids_path: {display_path(resolve_input_path(args.selected_ids_path))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
