"""Create a prompt for regenerating C++ code from a design document."""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT_DIR = ROOT_DIR / "experiments" / "humanevalx_cpp"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a C++ code-generation prompt from a local LLM design document."
    )
    parser.add_argument("--problem-id", default="problem_000", help="Problem ID to process.")
    parser.add_argument(
        "--experiment-dir",
        type=Path,
        default=DEFAULT_EXPERIMENT_DIR,
        help="Experiment directory. Defaults to experiments/humanevalx_cpp.",
    )
    parser.add_argument(
        "--design-file",
        type=Path,
        default=None,
        help="Optional path to the generated design document.",
    )
    return parser.parse_args()


def build_prompt(problem_id: str, design_text: str) -> str:
    return f"""以下の設計書に基づいて、C++ の関数実装だけを生成してください。

制約:
- 出力は C++ コードだけにしてください。
- `main` 関数、テストコード、説明文、Markdown のコードフェンスは含めないでください。
- 設計書にある関数シグネチャを維持してください。
- 標準ライブラリが不要な場合は include を追加しないでください。

対象問題 ID: {problem_id}

設計書:
{design_text}
"""


def main() -> int:
    args = parse_args()
    problem_dir = args.experiment_dir / "problems" / args.problem_id
    design_path = args.design_file or (problem_dir / "generated_design" / "design.md")
    prompt_path = problem_dir / "prompts" / "codegen_prompt.txt"

    if not design_path.exists():
        print("Generated design document not found.")
        print(f"Save the local LLM design output here first: {design_path}")
        return 1

    design_text = design_path.read_text(encoding="utf-8")
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(build_prompt(args.problem_id, design_text), encoding="utf-8")
    print(f"Wrote code-generation prompt: {prompt_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
