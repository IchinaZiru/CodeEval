"""Create a prompt for generating a design document from original C++ code."""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT_DIR = ROOT_DIR / "experiments" / "humanevalx_cpp"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a design-document prompt for one dummy problem."
    )
    parser.add_argument("--problem-id", default="problem_000", help="Problem ID to process.")
    parser.add_argument(
        "--experiment-dir",
        type=Path,
        default=DEFAULT_EXPERIMENT_DIR,
        help="Experiment directory. Defaults to experiments/humanevalx_cpp.",
    )
    return parser.parse_args()


def build_prompt(problem_id: str, source_code: str) -> str:
    return f"""以下の C++ 正解実装を読み、同じ関数を再実装できる設計書を作成してください。

制約:
- C++ コードそのものは出力しないでください。
- 関数名、引数、返り値、処理内容、境界条件、想定される計算量を記述してください。
- 元コードの変数名や実装細部をそのまま写すのではなく、仕様として説明してください。
- 出力は Markdown の設計書だけにしてください。

対象問題 ID: {problem_id}

```cpp
{source_code}
```
"""


def main() -> int:
    args = parse_args()
    problem_dir = args.experiment_dir / "problems" / args.problem_id
    original_path = problem_dir / "original.cpp"
    prompt_path = problem_dir / "prompts" / "design_prompt.txt"

    if not original_path.exists():
        print(f"Original source not found: {original_path}")
        return 1

    source_code = original_path.read_text(encoding="utf-8")
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(build_prompt(args.problem_id, source_code), encoding="utf-8")
    print(f"Wrote design prompt: {prompt_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
