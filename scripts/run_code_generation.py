"""Generate C++ code by sending codegen_prompt.txt to Ollama."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from make_codegen_prompt import build_prompt
from ollama_client import DEFAULT_OLLAMA_URL, OllamaClient, OllamaClientError


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT_DIR = ROOT_DIR / "experiments" / "humanevalx_cpp"
DEFAULT_PROMPT_VERSION = "prompt_v2_signature_include"


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT_DIR).as_posix()
    except ValueError:
        return str(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Call Ollama to generate C++ code from codegen_prompt.txt."
    )
    parser.add_argument("--problem-id", default="problem_000", help="Problem ID to process.")
    parser.add_argument("--model", required=True, help="Ollama model name, for example qwen2.5-coder:7b.")
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Ollama generation temperature. Defaults to 0.",
    )
    parser.add_argument(
        "--ollama-url",
        default=DEFAULT_OLLAMA_URL,
        help=f"Ollama base URL. Defaults to {DEFAULT_OLLAMA_URL}.",
    )
    parser.add_argument(
        "--ollama-timeout",
        type=float,
        default=120.0,
        help="Ollama request timeout in seconds. Defaults to 120.",
    )
    parser.add_argument(
        "--prompt-version",
        default=DEFAULT_PROMPT_VERSION,
        help=f"Prompt version label to record in metadata. Defaults to {DEFAULT_PROMPT_VERSION}.",
    )
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


def refresh_codegen_prompt(problem_id: str, problem_dir: Path, prompt_version: str) -> Path:
    design_path = problem_dir / "generated_design" / "design.md"
    prompt_path = problem_dir / "prompts" / "codegen_prompt.txt"

    if not design_path.exists():
        raise FileNotFoundError(
            f"Generated design document not found: {design_path}. "
            "Run run_design_generation.py first or save local LLM output there."
        )

    design_text = design_path.read_text(encoding="utf-8")
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(build_prompt(problem_id, design_text, prompt_version), encoding="utf-8")
    return prompt_path


def extract_cpp_code(text: str) -> str:
    """Return the inside of a fenced C++ block, or the original text if none exists."""
    cpp_fence = re.search(r"```(?:cpp|c\+\+|cc|cxx)\s*\n(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
    if cpp_fence:
        return cpp_fence.group(1).strip()

    any_fence = re.search(r"```\s*(?:\n)?(.*?)```", text, flags=re.DOTALL)
    if any_fence:
        return any_fence.group(1).strip()

    return text.strip()


def main() -> int:
    args = parse_args()
    problem_dir = args.experiment_dir / "problems" / args.problem_id
    output_path = problem_dir / "generated_code" / "generated.cpp"
    metadata_path = problem_dir / "results" / "code_generation_metadata.json"

    try:
        prompt_path = refresh_codegen_prompt(args.problem_id, problem_dir, args.prompt_version)
    except FileNotFoundError as exc:
        print(exc)
        return 1

    prompt = prompt_path.read_text(encoding="utf-8")
    client = OllamaClient(base_url=args.ollama_url, timeout=args.ollama_timeout)

    try:
        generated_text = client.generate(
            model=args.model,
            prompt=prompt,
            temperature=args.temperature,
        )
    except OllamaClientError as exc:
        print(f"Ollama code generation failed: {exc}")
        return 1

    code_text = extract_cpp_code(generated_text)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(code_text.rstrip() + "\n", encoding="utf-8")

    write_json(
        metadata_path,
        {
            "problem_id": args.problem_id,
            "model": args.model,
            "temperature": args.temperature,
            "ollama_timeout": args.ollama_timeout,
            "ollama_url": args.ollama_url,
            "prompt_version": args.prompt_version,
            "prompt_path": display_path(prompt_path),
            "output_path": display_path(output_path),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

    print(f"Wrote generated C++ code: {output_path}")
    print(f"Wrote metadata: {metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
