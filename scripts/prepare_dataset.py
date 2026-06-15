"""Prepare HumanEval-X C++ records for the CodeEval problem layout.

Step 2 can materialize metadata.json, original.cpp, spec.md, and empty support
directories. It intentionally does not create test.cpp or generated artifacts.
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
        description="Validate, select, and optionally materialize HumanEval-X C++ records."
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
        help="Print selected mapping and planned files without writing anything.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate metadata.json, original.cpp, and spec.md if a problem directory already exists.",
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
            parsed["_source_index"] = len(records)
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


def selected_items(
    selected_records: list[dict[str, Any]],
    *,
    start_index: int,
    task_ids: list[str] | None,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for offset, record in enumerate(selected_records):
        source_index = int(record["_source_index"])
        problem_id = codeeval_problem_id(offset)
        items.append(
            {
                "problem_id": problem_id,
                "source_index": source_index,
                "record": record,
            }
        )
    return items


def print_selection(raw_jsonl: Path, items: list[dict[str, Any]]) -> None:
    print(f"Selected {len(items)} problems from {display_path(raw_jsonl)}")
    print()
    for item in items:
        print(f"{item['problem_id']} <- {item['record']['task_id']}")


def planned_paths(problem_dir: Path) -> list[Path]:
    return [
        problem_dir / "metadata.json",
        problem_dir / "original.cpp",
        problem_dir / "spec.md",
        problem_dir / "prompts",
        problem_dir / "generated_design",
        problem_dir / "generated_code",
        problem_dir / "results",
    ]


def print_dry_run_plan(experiment_dir: Path, items: list[dict[str, Any]]) -> None:
    print()
    print("Dry-run: planned materialization")
    for item in items:
        problem_dir = experiment_dir / "problems" / item["problem_id"]
        print()
        print(f"{item['problem_id']} ({item['record']['task_id']})")
        for path in planned_paths(problem_dir):
            print(f"  - {display_path(path)}")


def ensure_safe_to_materialize(problem_dir: Path, force: bool) -> None:
    if not problem_dir.exists() or force:
        return

    raise DatasetPreparationError(
        f"Problem directory already exists and --force was not specified: {display_path(problem_dir)}"
    )


def metadata_payload(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "problem_id": item["problem_id"],
        "source": "HumanEval-X",
        "language": "cpp",
        "task_id": item["record"]["task_id"],
        "source_index": item["source_index"],
    }


def original_cpp(record: dict[str, Any]) -> str:
    declaration = str(record["declaration"]).rstrip()
    canonical_solution = str(record["canonical_solution"]).strip("\n")
    return f"{declaration}\n{canonical_solution}\n"


def spec_md(item: dict[str, Any]) -> str:
    record = item["record"]
    return f"""# {item['problem_id']}

- source: HumanEval-X
- language: cpp
- task_id: {record['task_id']}
- source_index: {item['source_index']}

## 注意

この `spec.md` は人間確認用のメタ情報です。
`make_design_prompt.py` はこのファイルではなく `original.cpp` を入力にして設計書生成プロンプトを作成します。

## prompt

```text
{record['prompt'].rstrip()}
```

## declaration

```cpp
{record['declaration'].rstrip()}
```
"""


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def materialize_problem(experiment_dir: Path, item: dict[str, Any], force: bool) -> None:
    problem_dir = experiment_dir / "problems" / item["problem_id"]
    ensure_safe_to_materialize(problem_dir, force)

    for directory_name in ["prompts", "generated_design", "generated_code", "results"]:
        (problem_dir / directory_name).mkdir(parents=True, exist_ok=True)

    metadata_path = problem_dir / "metadata.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata_payload(item), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_text(problem_dir / "original.cpp", original_cpp(item["record"]))
    write_text(problem_dir / "spec.md", spec_md(item))


def materialize_problems(experiment_dir: Path, items: list[dict[str, Any]], force: bool) -> None:
    for item in items:
        problem_dir = experiment_dir / "problems" / item["problem_id"]
        ensure_safe_to_materialize(problem_dir, force)

    for item in items:
        materialize_problem(experiment_dir, item, force)


def print_materialized(experiment_dir: Path, items: list[dict[str, Any]]) -> None:
    print()
    for item in items:
        problem_dir = experiment_dir / "problems" / item["problem_id"]
        print(f"Materialized {display_path(problem_dir)}")


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
        items = selected_items(
            selected_records,
            start_index=args.start_index,
            task_ids=args.task_ids,
        )
    except DatasetPreparationError as exc:
        print(exc)
        return 1

    experiment_dir = resolve_input_path(args.experiment_dir)
    print_selection(raw_jsonl, items)

    if args.dry_run:
        print_dry_run_plan(experiment_dir, items)
        return 0

    try:
        materialize_problems(experiment_dir, items, args.force)
    except DatasetPreparationError as exc:
        print(exc)
        return 1

    print_materialized(experiment_dir, items)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
