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


def resolve_existing_path(path: Path) -> Path:
    return path.resolve() if path.exists() else path.absolute()


def resolve_compiler(compiler: str) -> Path | None:
    compiler_path = Path(compiler)
    if compiler_path.exists():
        return compiler_path.resolve()

    found = shutil.which(compiler)
    return Path(found).resolve() if found else None


def path_entries() -> list[str]:
    return [entry for entry in os.environ.get("PATH", "").split(os.pathsep) if entry]


def build_subprocess_env(compiler_path: Path | None) -> tuple[dict[str, str], bool]:
    env = os.environ.copy()
    if compiler_path is None:
        return env, False

    compiler_dir = str(compiler_path.parent)
    current_entries = env.get("PATH", "").split(os.pathsep)
    if any(entry.lower() == compiler_dir.lower() for entry in current_entries):
        return env, False

    env["PATH"] = compiler_dir + os.pathsep + env.get("PATH", "")
    return env, True


def compiler_probe(compiler_command: str, env: dict[str, str], timeout: float) -> dict[str, Any]:
    try:
        result = subprocess.run(
            [compiler_command, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    except Exception as exc:
        return {
            "status": "failed_to_run",
            "error": f"{type(exc).__name__}: {exc}",
        }

    return {
        "status": "ran",
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def base_payload(args: argparse.Namespace, problem_dir: Path) -> dict[str, Any]:
    generated_path = problem_dir / "generated_code" / "generated.cpp"
    test_path = problem_dir / "test.cpp"
    compiler_path = resolve_compiler(args.compiler)

    return {
        "problem_id": args.problem_id,
        "compiler": args.compiler,
        "compiler_exists": compiler_path is not None,
        "compiler_resolved_path": str(compiler_path) if compiler_path else None,
        "compiler_parent": str(compiler_path.parent) if compiler_path else None,
        "cwd": str(ROOT_DIR),
        "test_path": display_path(test_path),
        "test_abs_path": str(resolve_existing_path(test_path)),
        "generated_path": display_path(generated_path),
        "generated_abs_path": str(resolve_existing_path(generated_path)),
    }


def main() -> int:
    args = parse_args()
    experiment_dir = args.experiment_dir.resolve()
    problem_dir = experiment_dir / "problems" / args.problem_id
    generated_path = resolve_existing_path(problem_dir / "generated_code" / "generated.cpp")
    test_path = resolve_existing_path(problem_dir / "test.cpp")
    result_path = problem_dir / "results" / "test_results.json"
    build_dir = problem_dir / "results" / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    executable = (build_dir / ("test_generated.exe" if os.name == "nt" else "test_generated")).resolve()
    compiler_path = resolve_compiler(args.compiler)
    compiler_command = str(compiler_path) if compiler_path else args.compiler
    subprocess_env, compiler_parent_added = build_subprocess_env(compiler_path)

    payload = base_payload(args, problem_dir)
    payload.update(
        {
            "build_dir": str(build_dir.resolve()),
            "executable_path": str(executable),
            "compiler_parent_added_to_path": compiler_parent_added,
            "path_contains_compiler_parent": bool(
                compiler_path
                and any(entry.lower() == str(compiler_path.parent).lower() for entry in path_entries())
            ),
        }
    )

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

    if compiler_path is None:
        payload.update(
            {
                "status": "compiler_not_found",
                "passed": False,
                "reason": f"Compiler not found: {args.compiler}",
                "diagnostic": (
                    "Pass an absolute compiler path, or add the compiler directory to PATH. "
                    "For MSYS2 UCRT64 this is usually C:\\msys64\\ucrt64\\bin."
                ),
            }
        )
        write_json(result_path, payload)
        print(payload["reason"])
        return 1

    payload["compiler_probe"] = compiler_probe(compiler_command, subprocess_env, args.timeout)
    compile_cmd = [
        compiler_command,
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
            cwd=str(ROOT_DIR),
            env=subprocess_env,
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
        diagnostic = "Compilation failed. Check compile_stderr and compile_stdout."
        if not compile_result.stdout and not compile_result.stderr:
            diagnostic = (
                "Compilation returned a nonzero exit code with empty stdout/stderr. "
                "On Windows/MSYS2 this commonly happens when g++.exe starts but one of its "
                "runtime DLLs or helper tools is not found in PATH. This script prepends the "
                "compiler directory to PATH when an absolute compiler path exists; verify "
                "compiler_parent_added_to_path, compiler_probe, and compiler_resolved_path."
            )
        payload.update(
            {
                "status": "compile_failed",
                "passed": False,
                "diagnostic": diagnostic,
            }
        )
        write_json(result_path, payload)
        print(f"Compilation failed. See {result_path}")
        print(diagnostic)
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
            cwd=str(ROOT_DIR),
            env=subprocess_env,
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
