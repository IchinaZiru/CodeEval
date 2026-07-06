"""Create a prompt for regenerating C++ code from a design document."""

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
    "prompt_v4_general_design_self_check",
)


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
    parser.add_argument(
        "--prompt-version",
        choices=SUPPORTED_PROMPT_VERSIONS,
        default=DEFAULT_PROMPT_VERSION,
        help=f"Code-generation prompt version. Defaults to {DEFAULT_PROMPT_VERSION}.",
    )
    return parser.parse_args()


def build_v2_prompt(problem_id: str, design_text: str) -> str:
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


def build_v4_prompt(problem_id: str, design_text: str) -> str:
    return f"""以下の設計書に基づいて、C++ の関数実装だけを生成してください。

制約:
- 出力は C++ コードだけにしてください。
- Markdown、code fence、説明文、テストコード、`main` 関数は出力しないでください。
- 出力先は `generated.cpp` です。`generated.cpp` は、リポジトリの `test.cpp` と一緒にコンパイルされる独立した translation unit として成立する必要があります。
- 関数シグネチャまたは実装で必要な標準ライブラリの include は、`generated.cpp` 内に必ず出力してください。必要に応じて `#include <vector>`、`#include <string>`、`#include <algorithm>`、`#include <cmath>`、`#include <numeric>`、`#include <set>`、`#include <map>`、`#include <tuple>`、`#include <utility>` などを含めてください。
- `generated.cpp` は `test.cpp` 側の include に依存してはいけません。
- 設計書の正確なシグネチャが `vector`、`string`、`map`、`set`、`tuple`、`pair` などの非修飾の標準ライブラリ名を使っている場合は、そのシグネチャを変更せずにコンパイルできるよう、必要な include と namespace 対応を必ず追加してください。
- 重要: `#include <vector>` だけでは `vector<float>` という非修飾名は使えません。シグネチャに `vector<float>` のような非修飾標準型がある場合は、include の後、関数定義の前に `using namespace std;` を出力してください。
- 設計書のシグネチャが `std::vector<float>` のように `std::` 付きなら、その `std::` を維持してください。この場合は `vector<float>` に変えないでください。
- namespace qualification を勝手に変更しないでください。設計書が `vector<int> xs` なら `vector<int> xs` のまま、`std::vector<int> xs` なら `std::vector<int> xs` のまま出力してください。
- 設計書にある関数シグネチャを完全一致で維持してください。
- 返り値の型、関数名、引数の順序、引数名、引数の型、値渡し、reference、const の有無を変更しないでください。
- 値渡しを勝手に const reference に変更しないでください。設計書が `std::string s` なら `const std::string& s` にせず、`vector<int> xs` なら `const vector<int>& xs` にしないでください。
- overload、補助 API、class、namespace、別名の関数を作らないでください。

最終出力前の self-check:
- 以下の self-check は内部確認だけに使ってください。self-check の結果、チェックリスト、説明文は出力しないでください。
- `generated.cpp` は単体の translation unit としてコンパイル可能か確認してください。
- 使用している標準ライブラリ型や関数に対応する `#include` があるか確認してください。
- `vector` を使うなら `#include <vector>` があるか確認してください。
- `string` を使うなら `#include <string>` があるか確認してください。
- `map` を使うなら `#include <map>` があるか確認してください。
- `set` を使うなら `#include <set>` があるか確認してください。
- `tuple` を使うなら `#include <tuple>` があるか確認してください。
- `pair` などを使うなら `#include <utility>` があるか確認してください。
- `sort`、`reverse`、`max`、`min` などを使うなら `#include <algorithm>` があるか確認してください。
- `abs`、`sqrt`、`pow` などを使うなら `#include <cmath>` があるか確認してください。
- `accumulate` などを使うなら `#include <numeric>` があるか確認してください。
- `std::` を使う方針か `using namespace std;` を使う方針かが一貫しているか確認してください。
- シグネチャや実装で `vector`、`string`、`map`、`set`、`tuple`、`pair` などを非修飾で使っている場合、include の後、関数定義の前に `using namespace std;` があるか確認してください。
- `#include <vector>` があっても `using namespace std;` または適切な `std::` がなければ `vector<float>` はコンパイルできないことを確認してください。
- 設計書が `vector<float>` のような非修飾シグネチャを指定している場合、`std::vector<float>` に変更せず、`using namespace std;` を追加して完全一致のシグネチャを守ってください。
- 設計書に書かれた C++ 関数シグネチャと完全一致しているか確認してください。
- 返り値の型を変えていないか確認してください。
- 関数名を変えていないか確認してください。
- 引数の順序、名前、型を変えていないか確認してください。
- 値渡しを const reference に勝手に変更していないか確認してください。
- reference や const の有無を変更していないか確認してください。
- 余計な `main` 関数を出力していないか確認してください。
- テストコードを出力していないか確認してください。
- Markdown code fence を出力していないか確認してください。
- 最終出力が C++ コードのみになっているか確認してください。

対象問題 ID: {problem_id}

設計書:
{design_text}
"""


def build_prompt(
    problem_id: str,
    design_text: str,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
) -> str:
    if prompt_version == "prompt_v4_general_design_self_check":
        return build_v4_prompt(problem_id, design_text)
    if prompt_version in {
        "prompt_v2_signature_include",
        "prompt_v3_general_design",
        "prompt_v3_general_design_v2",
    }:
        return build_v2_prompt(problem_id, design_text)
    raise ValueError(f"Unsupported prompt version: {prompt_version}")


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
    prompt_path.write_text(
        build_prompt(args.problem_id, design_text, args.prompt_version),
        encoding="utf-8",
    )
    print(f"Wrote code-generation prompt: {prompt_path}")
    print(f"Prompt version: {args.prompt_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
