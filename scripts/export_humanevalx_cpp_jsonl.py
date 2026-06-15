"""Export the HumanEval-X C++ subset from Hugging Face datasets to local JSONL."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_NAME = "THUDM/humaneval-x"
FALLBACK_DATASET_NAMES = ["zai-org/humaneval-x"]
DEFAULT_SUBSET = "cpp"
DEFAULT_SPLIT = "test"
DEFAULT_OUTPUT = ROOT_DIR / "data" / "raw" / "humanevalx_cpp" / "humaneval_cpp.jsonl"
REQUIRED_FIELDS = [
    "task_id",
    "prompt",
    "declaration",
    "canonical_solution",
    "test",
    "example_test",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export HumanEval-X C++ from Hugging Face datasets to local JSONL."
    )
    parser.add_argument(
        "--dataset-name",
        default=DEFAULT_DATASET_NAME,
        help=f"Hugging Face dataset name. Defaults to {DEFAULT_DATASET_NAME}.",
    )
    parser.add_argument(
        "--subset",
        default=DEFAULT_SUBSET,
        help=f"Dataset subset/config. Defaults to {DEFAULT_SUBSET}.",
    )
    parser.add_argument(
        "--split",
        default=DEFAULT_SPLIT,
        help=f"Dataset split. Defaults to {DEFAULT_SPLIT}.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output JSONL path. Defaults to data/raw/humanevalx_cpp/humaneval_cpp.jsonl.",
    )
    return parser.parse_args()


def import_load_dataset() -> Any:
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise RuntimeError(
            "The 'datasets' package is not installed. "
            "Install it with: pip install -r requirements-dataset.txt"
        ) from exc
    return load_dataset


def load_raw_jsonl_from_hub(dataset_name: str, subset: str) -> Any:
    """Fallback for datasets versions that no longer execute dataset scripts."""
    load_dataset = import_load_dataset()
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:
        raise RuntimeError(
            "The 'huggingface_hub' package is required for raw JSONL fallback. "
            "It is installed automatically with datasets."
        ) from exc

    filename = f"data/{subset}/data/humaneval.jsonl"
    local_path = hf_hub_download(
        repo_id=dataset_name,
        filename=filename,
        repo_type="dataset",
    )
    return load_dataset("json", data_files=local_path, split="train")


def load_humanevalx_dataset(dataset_name: str, subset: str, split: str) -> Any:
    load_dataset = import_load_dataset()
    candidate_names = [dataset_name]
    if dataset_name == DEFAULT_DATASET_NAME:
        candidate_names.extend(name for name in FALLBACK_DATASET_NAMES if name not in candidate_names)

    errors: list[str] = []
    for candidate_name in candidate_names:
        try:
            return load_dataset(candidate_name, subset, split=split)
        except Exception as exc:  # Hugging Face raises several exception types.
            errors.append(f"{candidate_name}: {type(exc).__name__}: {exc}")
            if split == DEFAULT_SPLIT:
                try:
                    return load_raw_jsonl_from_hub(candidate_name, subset)
                except Exception as fallback_exc:
                    errors.append(
                        f"{candidate_name} raw JSONL fallback: "
                        f"{type(fallback_exc).__name__}: {fallback_exc}"
                    )

    joined_errors = "\n".join(f"- {error}" for error in errors)
    raise RuntimeError(f"Could not load HumanEval-X dataset.\n{joined_errors}")


def validate_record(record: dict[str, Any], index: int) -> None:
    missing = [field for field in REQUIRED_FIELDS if field not in record]
    if missing:
        missing_text = ", ".join(missing)
        task_id = record.get("task_id", f"row {index}")
        raise ValueError(f"Record {task_id} is missing required field(s): {missing_text}")


def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    return {field: record[field] for field in REQUIRED_FIELDS}


def write_jsonl(records: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> int:
    args = parse_args()
    output_path = args.output if args.output.is_absolute() else ROOT_DIR / args.output

    dataset = load_humanevalx_dataset(args.dataset_name, args.subset, args.split)
    records: list[dict[str, Any]] = []

    for index, row in enumerate(dataset):
        record = dict(row)
        validate_record(record, index)
        records.append(normalize_record(record))

    write_jsonl(records, output_path)
    print(f"Saved {len(records)} records to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
