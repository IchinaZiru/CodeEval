"""Compile generated C++ code with the dummy test harness and run it."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
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
        description="Compile generated.cpp with test.cpp and run the resulting executable."
    )
    parser.add_argument("--problem-id", default="problem_000", help="Problem ID to process.")
    parser.add_argument(
        "--experiment-dir",
        type=Path,
        default=DEFAULT_EXPERIMENT_DIR,
        help="Experiment directory. Defaults to experiments/humanevalx_cpp.",
    )
    parser.add_argument(
        "--compiler",
        default="g++",
        help="C++ compiler command or path. Defaults to g++.",
    )
    parser.add_argument(
        "--std",
        default="c++17",
        help="C++ standard passed to the compiler. Defaults to c++17.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Compile and execution timeout in seconds.",
    )
    return parser.parse_args()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def base_payload(args: argparse.Namespace, problem_dir: Path) -> dict[str, Any]:
    return {
        "problem_id": args.problem_id,
        "compiler": args.compiler,
        "test_path": display_path(problem_dir / "test.cpp"),
        "generated_path": display_path(problem_dir / "generated_code" / "generated.cpp"),
    }


def main() -> int:
    args = parse_args()
    problem_dir = args.experiment_dir / "problems" / args.problem_id
    generated_path = problem_dir / "generated_code" / "generated.cpp"
    test_path = problem_dir / "test.cpp"
    result_path = problem_dir / "results" / "test_results.json"
    build_dir = problem_dir / "results" / "build"
    executable = build_dir / ("test_generated.exe" if os.name == "nt" else "test_generated")

    payload = base_payload(args, problem_dir)

    if not generated_path.exists():
        payload.update(
            {
                "status": "missing_generated_code",
                "passed": False,
                "reason": f"Save local LLM output to {generated_path} first.",
            }
        )
        write_json(result_path, payload)
        print(payload["reason"])
        return 1

    if not test_path.exists():
        payload.update(
            {
                "status": "missing_test",
                "passed": False,
                "reason": f"Test source not found: {test_path}",
            }
        )
        write_json(result_path, payload)
        print(payload["reason"])
        return 1

    if shutil.which(args.compiler) is None and not Path(args.compiler).exists():
        payload.update(
            {
                "status": "compiler_not_found",
                "passed": False,
                "reason": f"Compiler not found: {args.compiler}",
            }
        )
        write_json(result_path, payload)
        print(payload["reason"])
        return 1

    build_dir.mkdir(parents=True, exist_ok=True)
    compile_cmd = [
        args.compiler,
        f"-std={args.std}",
        str(generated_path),
        str(test_path),
        "-o",
        str(executable),
    ]
    payload["compile_command"] = compile_cmd

    try:
        compile_result = subprocess.run(
            compile_cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=args.timeout,
        )
    except subprocess.TimeoutExpired as exc:
        payload.update(
            {
                "status": "compile_timeout",
                "passed": False,
                "reason": f"Compilation timed out after {args.timeout} seconds.",
                "stdout": exc.stdout or "",
                "stderr": exc.stderr or "",
            }
        )
        write_json(result_path, payload)
        print(payload["reason"])
        return 1

    payload.update(
        {
            "compile_returncode": compile_result.returncode,
            "compile_stdout": compile_result.stdout,
            "compile_stderr": compile_result.stderr,
        }
    )

    if compile_result.returncode != 0:
        payload.update({"status": "compile_failed", "passed": False})
        write_json(result_path, payload)
        print(f"Compilation failed. See {result_path}")
        return 1

    run_cmd = [str(executable)]
    payload["run_command"] = run_cmd
    try:
        run_result = subprocess.run(
            run_cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=args.timeout,
        )
    except subprocess.TimeoutExpired as exc:
        payload.update(
            {
                "status": "run_timeout",
                "passed": False,
                "reason": f"Test execution timed out after {args.timeout} seconds.",
                "stdout": exc.stdout or "",
                "stderr": exc.stderr or "",
            }
        )
        write_json(result_path, payload)
        print(payload["reason"])
        return 1

    passed = run_result.returncode == 0
    payload.update(
        {
            "status": "passed" if passed else "test_failed",
            "passed": passed,
            "run_returncode": run_result.returncode,
            "run_stdout": run_result.stdout,
            "run_stderr": run_result.stderr,
        }
    )
    write_json(result_path, payload)
    print(f"Wrote test result: {result_path}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
