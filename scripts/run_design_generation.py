"""Generate a design document by sending design_prompt.txt to Ollama."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ollama_client import DEFAULT_OLLAMA_URL, OllamaClient, OllamaClientError


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT_DIR = ROOT_DIR / "experiments" / "humanevalx_cpp"


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT_DIR).as_posix()
    except ValueError:
        return str(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Call Ollama to generate a design document from design_prompt.txt."
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
        "--timeout",
        type=float,
        default=120.0,
        help="Ollama request timeout in seconds. Defaults to 120.",
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


def main() -> int:
    args = parse_args()
    problem_dir = args.experiment_dir / "problems" / args.problem_id
    prompt_path = problem_dir / "prompts" / "design_prompt.txt"
    output_path = problem_dir / "generated_design" / "design.md"
    metadata_path = problem_dir / "results" / "design_generation_metadata.json"

    if not prompt_path.exists():
        print(f"Design prompt not found: {prompt_path}")
        print(f"Create it first: python scripts/make_design_prompt.py --problem-id {args.problem_id}")
        return 1

    prompt = prompt_path.read_text(encoding="utf-8")
    client = OllamaClient(base_url=args.ollama_url, timeout=args.timeout)

    try:
        generated_text = client.generate(
            model=args.model,
            prompt=prompt,
            temperature=args.temperature,
        )
    except OllamaClientError as exc:
        print(f"Ollama design generation failed: {exc}")
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(generated_text.rstrip() + "\n", encoding="utf-8")

    write_json(
        metadata_path,
        {
            "problem_id": args.problem_id,
            "model": args.model,
            "temperature": args.temperature,
            "ollama_url": args.ollama_url,
            "prompt_path": display_path(prompt_path),
            "output_path": display_path(output_path),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

    print(f"Wrote generated design: {output_path}")
    print(f"Wrote metadata: {metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
