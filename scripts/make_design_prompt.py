"""Create a prompt for generating a design document from original C++ code."""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT_DIR = ROOT_DIR / "experiments" / "humanevalx_cpp"
DEFAULT_PROMPT_VERSION = "prompt_v2_signature_include"
SUPPORTED_PROMPT_VERSIONS = (
    "prompt_v2_signature_include",
    "prompt_v3_general_design",
    "prompt_v3_general_design_v2",
)


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
- 特定の問題や HumanEval-X 固有の書き方に依存せず、一般的な C++ コードとして構造を読み取ってください。
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


def build_v3_general_design_v2_prompt(problem_id: str, source_code: str) -> str:
    return f"""以下の C++ 正解実装を読み、同じ仕様の C++ 関数を再実装できる汎用的な設計書を作成してください。

目的:
- 特定の問題や HumanEval-X 固有の書き方に依存せず、一般的な C++ コードとして構造を読み取ってください。
- 元コードの実装を丸写しするのではなく、別の実装者が同じ仕様を再実装できる設計情報として整理してください。
- 出力は Markdown の設計書だけにしてください。C++ の再実装コードは出力しないでください。
- 再実装者が、処理対象、無視する入力、状態更新、結果追加タイミング、境界条件を取り違えないように具体化してください。

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
9. 処理対象にする入力要素
10. 無視する要素、空白、区切り文字、非対象文字の扱い
11. 出力に含めるもの、含めないもの
12. 処理手順
13. 分岐条件
14. 比較条件が `<`, `<=`, `>`, `>=`, `==`, `!=` のどれに相当するか
15. 早期 return が必要な条件
16. ループ構造
17. ループ中の状態更新条件
18. 一時変数、カウンタ、フラグ、スタック、バッファなどの役割
19. 条件を満たしたときに結果へ追加するタイミング
20. 結果追加前後で状態をリセットする必要があるか
21. ループ終了後に追加処理が必要か
22. 最後に残った状態変数やバッファの扱い
23. 並び順が重要な場合、昇順、降順、元の順序維持のどれか
24. 再帰の有無
25. helper 関数や補助構造の有無
26. 空入力、単一要素、重複要素、境界値の扱い
27. edge case と境界条件
28. 入力制約や前提条件
29. 想定される時間計算量と空間計算量
30. 再実装時に間違えやすい注意点

処理仕様を具体化するときの注意:
- 入力が数値列、文字列、コンテナ、区間、ペア、ネスト構造などの場合でも、処理対象にする単位を明確にしてください。
- 空白、改行、区切り文字、記号、大小文字、負数、ゼロ、重複、空要素などを処理するか無視するかを、元コードから読み取れる範囲で明記してください。
- 結果を vector、string、数値、bool などへ蓄積する場合、追加する条件、追加する値、追加する順序を明記してください。
- 状態変数、カウンタ、フラグ、スタック、バッファは、初期値、更新条件、リセット条件、最後の処理を明記してください。
- 条件分岐や比較では、境界を含むかどうかが分かるように `<`, `<=`, `>`, `>=`, `==`, `!=` の意味を説明してください。
- 早期 return がある場合は、どの入力や状態で返すのか、返す値が何かを明記してください。
- ループ終了後に残ったバッファや一時状態を結果に反映する必要がある場合は、その条件とタイミングを明記してください。
- 特定の HumanEval-X 問題だけに合わせた説明ではなく、一般的な C++ 関数の再実装に必要な情報として整理してください。

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
    if prompt_version == "prompt_v3_general_design_v2":
        return build_v3_general_design_v2_prompt(problem_id, source_code)
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
        print("Dry-run: design prompt will not be written.")
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
