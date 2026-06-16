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
- Markdown、code fence、説明文、テストコード、`main` 関数は出力しないでください。
- 出力先は `generated.cpp` です。`generated.cpp` は、リポジトリの `test.cpp` と一緒にコンパイルされる独立した translation unit として成立する必要があります。
- 関数シグネチャまたは実装で必要な標準ライブラリの include は、`generated.cpp` 内に必ず出力してください。必要に応じて `#include <vector>`、`#include <string>`、`#include <algorithm>`、`#include <cmath>`、`#include <numeric>`、`#include <set>`、`#include <map>` などを含めてください。
- `generated.cpp` は `test.cpp` 側の include に依存してはいけません。
- 設計書の正確なシグネチャが `vector`、`string`、`map`、`set`、`tuple` などの非修飾の標準ライブラリ名を使っている場合は、そのシグネチャを変更せずにコンパイルできるよう、必要な include と `using namespace std;` などの namespace 対応を追加してください。
- namespace qualification を勝手に変更しないでください。設計書が `vector<int> xs` なら `vector<int> xs` のまま、`std::vector<int> xs` なら `std::vector<int> xs` のまま出力してください。
- 設計書にある関数シグネチャを完全一致で維持してください。
- 返り値の型、関数名、引数の順序、引数名、引数の型、値渡し、reference、const の有無を変更しないでください。
- 値渡しを勝手に const reference に変更しないでください。設計書が `std::string s` なら `const std::string& s` にせず、`vector<int> xs` なら `const vector<int>& xs` にしないでください。
- overload、補助 API、class、namespace、別名の関数を作らないでください。

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
