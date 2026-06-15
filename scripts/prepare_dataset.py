"""Prepare HumanEval-X C++ records for the CodeEval problem layout.

This materializes metadata.json, original.cpp, spec.md, test.cpp, and empty
support directories. It intentionally does not create generated artifacts.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
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
COMMON_TEST_INCLUDES = """#undef NDEBUG
#include <cassert>
#include <assert.h>
#include <algorithm>
#include <cmath>
#include <iostream>
#include <map>
#include <numeric>
#include <set>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

using namespace std;
"""


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
        help="Regenerate metadata.json, original.cpp, spec.md, and test.cpp if a problem directory already exists.",
    )
    parser.add_argument(
        "--validate-original",
        action="store_true",
        help="Compile and run original.cpp with test.cpp for each selected problem.",
    )
    parser.add_argument(
        "--compiler",
        default="g++",
        help="C++ compiler command or path for --validate-original. Defaults to g++.",
    )
    parser.add_argument(
        "--std",
        default="c++17",
        help="C++ standard for --validate-original. Defaults to c++17.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Compile and run timeout in seconds for --validate-original. Defaults to 10.",
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
        problem_dir / "test.cpp",
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


def original_validation_paths(experiment_dir: Path, problem_id: str) -> dict[str, Path]:
    problem_dir = experiment_dir / "problems" / problem_id
    executable_name = "original_test.exe" if os.name == "nt" else "original_test"
    return {
        "problem_dir": problem_dir,
        "original": problem_dir / "original.cpp",
        "test": problem_dir / "test.cpp",
        "result": problem_dir / "results" / "original_validation.json",
        "executable": problem_dir / "results" / executable_name,
    }


def resolve_compiler(compiler: str) -> Path | None:
    compiler_path = Path(compiler)
    if compiler_path.exists():
        return compiler_path.resolve()
    found = shutil.which(compiler)
    return Path(found).resolve() if found else None


def build_validation_env(compiler_path: Path | None) -> dict[str, str]:
    env = os.environ.copy()
    if compiler_path is None:
        return env

    compiler_dir = str(compiler_path.parent)
    path_entries = env.get("PATH", "").split(os.pathsep)
    if not any(entry.lower() == compiler_dir.lower() for entry in path_entries):
        env["PATH"] = compiler_dir + os.pathsep + env.get("PATH", "")
    return env


def original_compile_command(
    compiler_command: str,
    std: str,
    original_path: Path,
    test_path: Path,
    executable_path: Path,
) -> list[str]:
    return [
        compiler_command,
        f"-std={std}",
        str(original_path.resolve()),
        str(test_path.resolve()),
        "-o",
        str(executable_path.resolve()),
    ]


def print_original_validation_dry_run(
    experiment_dir: Path,
    items: list[dict[str, Any]],
    compiler: str,
    std: str,
) -> None:
    print()
    print("Dry-run: planned original validation commands")
    compiler_path = resolve_compiler(compiler)
    compiler_command = str(compiler_path) if compiler_path else compiler
    for item in items:
        paths = original_validation_paths(experiment_dir, item["problem_id"])
        command = original_compile_command(
            compiler_command,
            std,
            paths["original"],
            paths["test"],
            paths["executable"],
        )
        print()
        print(f"{item['problem_id']} ({item['record']['task_id']})")
        print("  compile: " + " ".join(command))
        print(f"  run: {display_path(paths['executable'])}")
        print(f"  result: {display_path(paths['result'])}")


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


def prototype_from_declaration(declaration: str) -> str:
    before_body = declaration.split("{", 1)[0]
    candidate_lines: list[str] = []

    for raw_line in before_body.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#") or line.startswith("using "):
            candidate_lines = []
            continue
        if line.startswith("//") or line.startswith("/*") or line.startswith("*"):
            continue
        candidate_lines.append(line)

    if not candidate_lines:
        raise DatasetPreparationError("Could not extract function prototype from declaration.")

    header = " ".join(candidate_lines)
    return header.rstrip(";") + ";"


def has_main_function(test_body: str) -> bool:
    return "int main" in test_body


def test_cpp(record: dict[str, Any]) -> str:
    prototype = prototype_from_declaration(str(record["declaration"]))
    test_body = str(record["test"]).strip()
    sections = [
        COMMON_TEST_INCLUDES.rstrip(),
        "",
        prototype,
        "",
        test_body,
    ]

    if not has_main_function(test_body):
        sections.extend(
            [
                "",
                "int main() {",
                "    check();",
                "    return 0;",
                "}",
            ]
        )

    return "\n".join(sections).rstrip() + "\n"


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
    write_text(problem_dir / "test.cpp", test_cpp(item["record"]))


def materialize_problems(experiment_dir: Path, items: list[dict[str, Any]], force: bool) -> None:
    for item in items:
        problem_dir = experiment_dir / "problems" / item["problem_id"]
        ensure_safe_to_materialize(problem_dir, force)

    for item in items:
        materialize_problem(experiment_dir, item, force)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_original_problem(
    experiment_dir: Path,
    item: dict[str, Any],
    compiler: str,
    std: str,
    timeout: float,
) -> dict[str, Any]:
    problem_id = item["problem_id"]
    paths = original_validation_paths(experiment_dir, problem_id)
    compiler_path = resolve_compiler(compiler)
    compiler_command = str(compiler_path) if compiler_path else compiler
    compile_command = original_compile_command(
        compiler_command,
        std,
        paths["original"],
        paths["test"],
        paths["executable"],
    )
    payload: dict[str, Any] = {
        "problem_id": problem_id,
        "compiler": compiler,
        "compiler_exists": compiler_path is not None,
        "compile_command": compile_command,
        "compile_returncode": None,
        "compile_stdout": "",
        "compile_stderr": "",
        "run_returncode": None,
        "run_stdout": "",
        "run_stderr": "",
        "passed": False,
        "status": "",
    }

    if compiler_path is None:
        payload["status"] = "compiler_not_found"
        write_json(paths["result"], payload)
        return payload

    paths["executable"].parent.mkdir(parents=True, exist_ok=True)
    env = build_validation_env(compiler_path)

    try:
        compile_result = subprocess.run(
            compile_command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(ROOT_DIR),
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        payload.update(
            {
                "status": "compile_timeout",
                "compile_stdout": exc.stdout or "",
                "compile_stderr": exc.stderr or "",
            }
        )
        write_json(paths["result"], payload)
        return payload

    payload.update(
        {
            "compile_returncode": compile_result.returncode,
            "compile_stdout": compile_result.stdout,
            "compile_stderr": compile_result.stderr,
        }
    )

    if compile_result.returncode != 0:
        payload["status"] = "compile_failed"
        write_json(paths["result"], payload)
        return payload

    try:
        run_result = subprocess.run(
            [str(paths["executable"].resolve())],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(ROOT_DIR),
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        payload.update(
            {
                "status": "run_timeout",
                "run_stdout": exc.stdout or "",
                "run_stderr": exc.stderr or "",
            }
        )
        write_json(paths["result"], payload)
        return payload

    passed = run_result.returncode == 0
    payload.update(
        {
            "run_returncode": run_result.returncode,
            "run_stdout": run_result.stdout,
            "run_stderr": run_result.stderr,
            "passed": passed,
            "status": "passed" if passed else "run_failed",
        }
    )
    write_json(paths["result"], payload)
    return payload


def validate_originals(
    experiment_dir: Path,
    items: list[dict[str, Any]],
    compiler: str,
    std: str,
    timeout: float,
) -> list[str]:
    failed_problem_ids: list[str] = []
    for item in items:
        result = validate_original_problem(experiment_dir, item, compiler, std, timeout)
        if result["status"] != "passed":
            failed_problem_ids.append(item["problem_id"])

    print()
    if failed_problem_ids:
        print("Original validation failed for:")
        for problem_id in failed_problem_ids:
            print(f"- {problem_id}")
    else:
        print("Original validation passed for all selected problems.")
    return failed_problem_ids


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
        if args.validate_original:
            print_original_validation_dry_run(experiment_dir, items, args.compiler, args.std)
        return 0

    try:
        materialize_problems(experiment_dir, items, args.force)
    except DatasetPreparationError as exc:
        print(exc)
        return 1

    print_materialized(experiment_dir, items)
    if args.validate_original:
        failed_problem_ids = validate_originals(
            experiment_dir,
            items,
            args.compiler,
            args.std,
            args.timeout,
        )
        return 1 if failed_problem_ids else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
