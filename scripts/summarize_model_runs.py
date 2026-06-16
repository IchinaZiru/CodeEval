"""Summarize multiple model-specific HumanEval-X C++ runs."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from evaluation_metrics import (
    COMBINED_SUMMARY_FIELDS,
    average,
    collect_run_rows,
    display_path,
    generation_failed_or_timeout_count,
    read_csv_rows,
    read_json,
    resolve_path,
    run_summary_metrics,
    status_counts,
    write_csv,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_RUNS_ROOT = ROOT_DIR / "experiments" / "humanevalx_cpp_runs"
DEFAULT_PROMPT_VERSION = "prompt_v2_signature_include"

MODEL_SUMMARY_FIELDS = [
    "prompt_version",
    "model_dir",
    "model",
    "total",
    "passed",
    "failed",
    "pass_rate",
    "compile_failed",
    "test_failed",
    "generation_failed_or_timeout",
    "average_text_similarity",
    "average_token_jaccard_similarity",
    "average_token_cosine_similarity",
    "average_dolos_similarity",
    "average_design_quality_score",
    "average_text_similarity_passed",
    "average_text_similarity_failed",
    "average_design_quality_score_passed",
    "average_design_quality_score_failed",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize model run metrics for one prompt version.")
    parser.add_argument(
        "--prompt-version",
        default=DEFAULT_PROMPT_VERSION,
        help=f"Prompt version directory. Defaults to {DEFAULT_PROMPT_VERSION}.",
    )
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=DEFAULT_RUNS_ROOT,
        help="Root directory for model-specific runs. Defaults to experiments/humanevalx_cpp_runs.",
    )
    parser.add_argument(
        "--models",
        nargs="*",
        default=None,
        help="Optional model directory names to include. Defaults to all directories under the prompt version.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory. Defaults to <runs-root>/<prompt-version>/summary.",
    )
    return parser.parse_args()


def model_dirs(prompt_dir: Path, requested_models: list[str] | None) -> list[Path]:
    if requested_models:
        return [prompt_dir / model for model in requested_models]
    return sorted(path for path in prompt_dir.iterdir() if path.is_dir() and path.name != "summary")


def run_model_name(model_dir: Path) -> str:
    metadata = read_json(model_dir / "run_metadata.json") or {}
    return str(metadata.get("model") or model_dir.name)


def passed_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("passed") is True]


def failed_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("passed") is not True]


def coerce_value(value: Any) -> Any:
    if value == "True":
        return True
    if value == "False":
        return False
    if isinstance(value, str) and value.strip():
        try:
            return float(value)
        except ValueError:
            return value
    return value


def load_combined_rows(model_dir: Path) -> list[dict[str, Any]]:
    with_dolos_path = model_dir / "summary" / "combined_summary_with_dolos.csv"
    combined_path = model_dir / "summary" / "combined_summary.csv"
    if with_dolos_path.exists():
        return [{key: coerce_value(value) for key, value in row.items()} for row in read_csv_rows(with_dolos_path)]
    if combined_path.exists():
        return [{key: coerce_value(value) for key, value in row.items()} for row in read_csv_rows(combined_path)]
    _, combined_rows = collect_run_rows(model_dir)
    return combined_rows


def model_summary_row(prompt_version: str, model_dir: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = run_summary_metrics(rows)
    counts = status_counts(rows)
    return {
        "prompt_version": prompt_version,
        "model_dir": model_dir.name,
        "model": run_model_name(model_dir),
        "total": metrics["total"],
        "passed": metrics["passed"],
        "failed": metrics["failed"],
        "pass_rate": metrics["pass_rate"],
        "compile_failed": counts.get("compile_failed", 0),
        "test_failed": counts.get("test_failed", 0) + counts.get("run_failed", 0),
        "generation_failed_or_timeout": generation_failed_or_timeout_count(rows),
        "average_text_similarity": metrics["average_text_similarity"],
        "average_token_jaccard_similarity": metrics["average_token_jaccard_similarity"],
        "average_token_cosine_similarity": metrics["average_token_cosine_similarity"],
        "average_dolos_similarity": metrics["average_dolos_similarity"],
        "average_design_quality_score": metrics["average_design_quality_score"],
        "average_text_similarity_passed": average(passed_rows(rows), "text_similarity"),
        "average_text_similarity_failed": average(failed_rows(rows), "text_similarity"),
        "average_design_quality_score_passed": average(passed_rows(rows), "design_quality_score"),
        "average_design_quality_score_failed": average(failed_rows(rows), "design_quality_score"),
    }


def markdown_table(rows: list[dict[str, Any]], fields: list[str]) -> str:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        values = [str(row.get(field, "")) for field in fields]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def write_markdown(path: Path, prompt_version: str, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = [
        f"# Model Summary: {prompt_version}",
        "",
        markdown_table(rows, MODEL_SUMMARY_FIELDS),
    ]
    path.write_text("\n".join(content), encoding="utf-8")


def main() -> int:
    args = parse_args()
    runs_root = resolve_path(args.runs_root)
    prompt_dir = runs_root / args.prompt_version
    output_dir = resolve_path(args.output_dir) if args.output_dir else prompt_dir / "summary"

    if not prompt_dir.exists():
        print(f"Prompt version directory not found: {display_path(prompt_dir)}")
        return 1

    all_problem_rows: list[dict[str, Any]] = []
    model_summary_rows: list[dict[str, Any]] = []

    for model_dir in model_dirs(prompt_dir, args.models):
        if not model_dir.exists():
            print(f"Model directory not found: {display_path(model_dir)}")
            return 1
        combined_rows = load_combined_rows(model_dir)
        for row in combined_rows:
            row["prompt_version"] = args.prompt_version
            row["model_dir"] = model_dir.name
            row["model"] = run_model_name(model_dir)
        all_problem_rows.extend(combined_rows)
        model_summary_rows.append(model_summary_row(args.prompt_version, model_dir, combined_rows))

    problem_fields = ["prompt_version", "model_dir", "model", *COMBINED_SUMMARY_FIELDS]
    model_summary_path = output_dir / "model_summary.csv"
    model_summary_md_path = output_dir / "model_summary.md"
    problem_results_path = output_dir / "problem_results.csv"

    write_csv(model_summary_path, model_summary_rows, MODEL_SUMMARY_FIELDS)
    write_markdown(model_summary_md_path, args.prompt_version, model_summary_rows)
    write_csv(problem_results_path, all_problem_rows, problem_fields)

    print(f"Wrote model summary: {display_path(model_summary_path)}")
    print(f"Wrote model summary markdown: {display_path(model_summary_md_path)}")
    print(f"Wrote problem results: {display_path(problem_results_path)}")
    print(f"Models summarized: {len(model_summary_rows)}")
    print(f"Problem rows summarized: {len(all_problem_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
