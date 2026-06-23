"""Create a prompt for generating a design document from original C++ code."""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT_DIR = ROOT_DIR / "experiments" / "humanevalx_cpp"
DEFAULT_PROMPT_VERSION = "prompt_v2_signature_include"
SUPPORTED_PROMPT_VERSIONS = ("prompt_v2_signature_include", "prompt_v3_general_design")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a design-document prompt for one HumanEval-X C++ problem."
    )
    parser.add_argument("--problem-id", default="problem_000", help="Problem ID to process.")
    parser.add_argument(
        "--prompt-version",
        choices=SUPPORTED_PROMPT_VERSIONS,
        default=DEFAULT_PROMPT_VERSION,
        help=f"Design prompt version. Defaults to {DEFAULT_PROMPT_VERSION}.",
    )
    parser.add_argument(
        "--experiment-dir",
        type=Path,
        default=DEFAULT_EXPERIMENT_DIR,
        help="Experiment directory. Defaults to experiments/humanevalx_cpp.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned output path and prompt preview without writing design_prompt.txt.",
    )
    return parser.parse_args()


def build_v2_prompt(problem_id: str, source_code: str) -> str:
    return f"""以下の C++ 正解実装を読み、同じ関数を再実装できる設計書を作成してください。

制約:
- 出力は Markdown の設計書だけにしてください。C++ の再実装コードは出力しないでください。
- 設計書には、後続の C++ コード生成で関数シグネチャを間違えないための情報を必ず含めてください。
- C++ の関数シグネチャは、元コードにある対象関数のシグネチャと完全一致させてください。
- 特に C++ の関数シグネチャは、Markdown の `cpp` code fence で明記してください。
- シグネチャでは、返り値の型、関数名、引数の順序、引数名、引数の型、値渡し、reference、const の有無を変更しないでください。
- 値渡しを勝手に const reference に変更しないでください。元コードが `std::string s` なら `const std::string& s` にせず、`vector<int> xs` なら `const vector<int>& xs` にしないでください。
- namespace qualification を勝手に変更しないでください。元コードが `vector<int> xs` なら `vector<int> xs` のまま、`std::vector<int> xs` なら `std::vector<int> xs` のままにしてください。
- overload、補助 API、class、namespace、別名の関数を作らないでください。
- 元コードの実装本体をそのまま写すのではなく、仕様として説明してください。

設計書には必ず以下の項目を含めてください。
- 関数名
- C++ の関数シグネチャ
- 引数名、型、意味
- 返り値の型と意味
- 処理内容
- 境界条件
- 想定される時間計算量と空間計算量

関数シグネチャの記載例:

```cpp
int add(int a, int b)
```

対象問題 ID: {problem_id}

C++ 正解実装:

```cpp
{source_code}
```
"""


def build_v3_prompt(problem_id: str, source_code: str) -> str:
    return f"""以下の C++ 正解実装を読み、同じ仕様の C++ 関数を再実装できる汎用的な設計書を作成してください。

目的:
- 特定の問題やこのデータセット固有の書き方に依存せず、一般的な C++ コードとして構造を読み取ってください。
- 元コードの実装を丸写しするのではなく、別の実装者が同じ仕様を再実装できる設計情報として整理してください。
- 出力は Markdown の設計書だけにしてください。C++ の再実装コードは出力しないでください。

関数インターフェースに関する制約:
- 対象関数の C++ 関数シグネチャを、元コードと完全一致させて Markdown の `cpp` code fence で明記してください。
- 返り値の型、関数名、引数の順序、引数名、引数の型、値渡し、reference、const の有無を変更しないでください。
- 値渡しを勝手に const reference に変更しないでください。
- namespace qualification を勝手に変更しないでください。元コードが `vector<int> xs` なら `vector<int> xs` のまま、`std::vector<int> xs` なら `std::vector<int> xs` のままにしてください。
- overload、別名の関数、不要な class、不要な namespace を設計に追加しないでください。

設計書に必ず含める項目:
1. 関数の役割
2. C++ 関数シグネチャ
3. 引数の型、名前、意味
4. 返り値の型、意味
5. 使用している標準ライブラリ型や関数
6. 再実装時に必要な `#include` 候補
7. `std::` または `using namespace std;` に関する注意
8. 値渡し、reference、const の扱い
9. 処理手順
10. 分岐条件
11. ループ構造
12. 再帰の有無
13. helper 関数や補助構造の有無
14. edge case と境界条件
15. 入力制約や前提条件
16. 想定される時間計算量と空間計算量
17. 再実装時に間違えやすい注意点

依存関係に関する注意:
- 元コードの `#include` を機械的に丸写しするのではなく、再実装に必要な標準ライブラリ依存として整理してください。
- 例えば `vector` を使うなら `#include <vector>`、`string` を使うなら `#include <string>`、`sort` を使うなら `#include <algorithm>`、`abs` や `sqrt` などを使うなら `#include <cmath>` のように、必要な候補を明記してください。
- `#include <bits/stdc++.h>` のような包括的な include ではなく、必要な標準ヘッダを個別に示してください。

関数シグネチャの記載例:

```cpp
int add(int a, int b)
```

対象問題 ID: {problem_id}

C++ 正解実装:

```cpp
{source_code}
```
"""


def build_prompt(problem_id: str, source_code: str, prompt_version: str = DEFAULT_PROMPT_VERSION) -> str:
    if prompt_version == "prompt_v2_signature_include":
        return build_v2_prompt(problem_id, source_code)
    if prompt_version == "prompt_v3_general_design":
        return build_v3_prompt(problem_id, source_code)
    raise ValueError(f"Unsupported prompt version: {prompt_version}")


def preview_text(text: str, max_chars: int = 1200) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n... [truncated]"


def main() -> int:
    args = parse_args()
    problem_dir = args.experiment_dir / "problems" / args.problem_id
    original_path = problem_dir / "original.cpp"
    prompt_path = problem_dir / "prompts" / "design_prompt.txt"

    if not original_path.exists():
        print(f"Original source not found: {original_path}")
        return 1

    source_code = original_path.read_text(encoding="utf-8")
    prompt = build_prompt(args.problem_id, source_code, args.prompt_version)

    if args.dry_run:
        print(f"Dry-run: design prompt will not be written.")
        print(f"problem_id: {args.problem_id}")
        print(f"prompt_version: {args.prompt_version}")
        print(f"source_path: {original_path}")
        print(f"output_path: {prompt_path}")
        print()
        print(preview_text(prompt))
        return 0

    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(prompt, encoding="utf-8")
    print(f"Wrote design prompt: {prompt_path}")
    print(f"Prompt version: {args.prompt_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
