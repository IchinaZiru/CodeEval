# prompt_v3 と prompt_v4 の実験計画

この文書は、`prompt_v3_general_design` と `prompt_v4_general_design_self_check` の目的、比較条件、評価方法、結果の読み方を整理するためのメモである。

実行コマンド、集計コマンド、`--force-run` の注意は `docs/experiments/run_commands.md` を参照する。

## 背景

このリポジトリでは、HumanEval-X C++ の正解実装 `original.cpp` から設計書 `design.md` を逆生成し、その設計書から C++ の `generated.cpp` を再生成する。

実験の中心は、Codex が設計書や C++ コードを作ることではない。Codex はパイプライン、プロンプト、評価スクリプト、結果整理を担当する。実際の設計書生成とコード生成は、Ollama 上で動くローカル LLM が行う。

v1 から v2 では、関数シグネチャ、include、namespace、`const reference` 化などの形式的な失敗を抑えるためにプロンプトを強化した。その結果、少数問題では pass@1 が大きく改善した。

一方で、v2 の設計書生成プロンプトは、特定のコード形式や HumanEval-X の書き方に合わせて情報を抽出しすぎている可能性がある。つまり、単にベンチマークに特化したプロンプトになっており、一般的な C++ コードを読み取る能力を評価できていない可能性がある。

そのため v3 では、特定の問題やデータセット固有の形式に寄せるのではなく、一般的な C++ コードに対して使える設計書逆生成プロンプトを目指す。

## v3 の目的

`prompt_v3_general_design` の目的は、HumanEval-X C++ 全体に対して、単一の汎用的な設計書生成プロンプトがどこまで機能するかを調べることである。

ここでいう汎用的とは、次の意味である。

- 問題ごとにプロンプトを変えない。
- モデルごとにプロンプトを変えない。
- 関数名やデータ構造に合わせた個別ルールを入れない。
- HumanEval-X 特有の書き方だけに依存しない。
- 一般的な C++ 関数を読むときに必要な観点を設計書に抽出させる。

v3 では、設計書生成プロンプトを改善対象にする。コード生成プロンプトは v2 相当のまま固定し、設計書の質が後段のコード再生成にどのような影響を与えるかを見る。

## v3 で検証したい問い

v3 では、次の研究上の問いを検証する。

1. 一般的な C++ コード読解観点を与えるだけで、HumanEval-X C++ の設計書を安定して生成できるか。
2. 設計書に正確な関数シグネチャ、引数、返り値、標準ライブラリ依存、境界条件、計算量を含めることで、コード再生成の成功率は上がるか。
3. 設計書の品質指標と pass@k の間に関係があるか。
4. モデルによって、設計書の読み取り能力とコード再生成能力にどの程度差が出るか。
5. 失敗が起きる場合、それは設計書の不足、コード生成時の形式ミス、アルゴリズムの誤りのどれに多いか。

## v3 で設計書に含めさせる内容

v3 の設計書生成プロンプトでは、次の情報を `design.md` に含めるよう指示する。

- 関数の役割
- C++ 関数シグネチャ
- 引数の型、名前、意味
- 返り値の型、意味
- 使用している標準ライブラリ型や関数
- 再実装時に必要な `#include` 候補
- `std::` または `using namespace std;` に関する注意
- 値渡し、reference、`const` の扱い
- 処理手順
- 分岐条件
- ループ構造
- 再帰の有無
- helper 関数や補助構造の有無
- edge case と境界条件
- 入力制約や前提条件
- 想定される時間計算量と空間計算量
- 再実装時に間違えやすい注意点

特に重要なのは、関数シグネチャを元コードと完全一致させることである。返り値の型、関数名、引数の順序、引数名、引数の型、値渡し、reference、`const` の有無を勝手に変更させない。

例えば、元コードが次のシグネチャなら、

```cpp
vector<int> parse_nested_parens(string paren_string)
```

設計書にも同じ形で書かせる。`const string& paren_string` のように勝手に変更させない。

## v3 でやらないこと

v3 では、次のことは行わない。

- 問題別にプロンプトを調整しない。
- 失敗した問題だけに特化したプロンプト修正をしない。
- モデル別にプロンプトを変えない。
- Codex が `design.md` や `generated.cpp` を手で修正しない。
- generated code の compile error を手で直さない。
- codegen prompt に self-check を追加しない。

v3 で変えるのは、基本的に設計書生成プロンプトである。コード生成プロンプト側の改善は v4 の対象にする。

## v3.1: prompt_v3_general_design_v2 の目的

`prompt_v3_general_design_v2` は、既存の `prompt_v3_general_design` を上書きせずに追加する v3.1 相当のプロンプトである。

v3.1 の目的は、v3 の汎用性を維持したまま、再実装に必要な具体性を補うことである。ここでいう具体性とは、特定の HumanEval-X 問題に合わせた個別ルールではなく、一般的な C++ 関数を再実装するときに必要になる処理対象、無視条件、状態更新、結果追加タイミング、ループ後処理などの情報である。

v3.1 でも codegen prompt は変更しない。codegen self-check は追加しない。設計書生成プロンプトの改善効果だけを見るためである。codegen self-check は v4 の対象として残す。

v3.1 で追加して設計書に含めさせる観点:

- 入力のうち処理対象にする要素
- 無視する要素、空白、区切り文字、非対象文字の扱い
- 出力に含めるもの、含めないもの
- 状態変数、カウンタ、フラグ、スタック、バッファ、一時変数の役割
- ループ中の状態更新条件
- 条件を満たしたときに結果へ追加するタイミング
- 結果追加前後で状態をリセットする必要があるか
- ループ終了後に追加処理が必要か
- 最後に残った状態変数やバッファの扱い
- 空入力、単一要素、重複要素、境界値の扱い
- 早期 return が必要な条件
- 比較条件が `<`, `<=`, `>`, `>=`, `==`, `!=` のどれに相当するか
- 並び順が重要な場合、昇順、降順、元の順序維持のどれか

v3.1 の比較条件:

```text
design prompt = prompt_v3_general_design_v2
codegen prompt = v3 と同じ
codegen self-check = なし
対象問題 = v3 と同じ10問
対象モデル = gpt-oss:20b, phi4:latest, qwen3-coder:latest
design temperature = 0.0
pass@1 temperature = 0.0
pass@3 temperature = 0.2
pass@3 samples = 3
```

v3.1 の実験結果は、既存 v3 と混ざらないように次へ保存する。

```text
experiments/humanevalx_cpp_runs/prompt_v3_general_design_v2/<model_dir>/
```

## v3 の評価方法

v3 の主指標は pass@1 と pass@3 である。

```text
pass@1:
  temperature = 0.0
  1回だけ生成
  その1回が test.cpp に通れば成功

pass@3:
  temperature = 0.2
  3回生成
  3回のうち1回でも test.cpp に通れば成功
```

pass@1 は、決定的に近い条件でどれだけ安定して正解を出せるかを見る。

pass@3 は、少し多様性を持たせたときに、同じ設計書から正解コードを引ける可能性があるかを見る。

ただし、pass@3 は問題単位の成功率である。3回中1回でも通れば、その問題は成功として数える。そのため、sample 単位の成功率も別に見る必要がある。

例:

```text
problem_000:
  sample_001: passed
  sample_002: compile_failed
  sample_003: passed

この場合:
  pass@3 = success
  sample単位では 2/3 success
```

## v3 で見る補助指標

pass@k だけでは、なぜ成功または失敗したかが分からない。そのため、次の補助指標を見る。

- compile success rate
- test pass rate
- sample 単位の pass rate
- failure reason
- `compile_failed`
- `run_failed`
- `test_failed`
- `missing_generated_code`
- `generation_failed`
- original.cpp と generated.cpp の text similarity
- token similarity
- signature exact match
- include likely complete
- design quality score
- design signature exact match
- design に include 情報が含まれているか
- design に namespace 方針が含まれているか
- design に value/reference/const の扱いが含まれているか
- design に complexity が含まれているか

v3 では、特に設計書の品質とコード生成成功率の関係を見る。

例えば、設計書に `#include <vector>` や `using namespace std;` の注意が書かれているのに `generated.cpp` で include が欠ける場合、原因は設計書ではなくコード生成側にある可能性が高い。

逆に、設計書に関数シグネチャや境界条件が欠けている場合、コード生成の失敗は設計書生成段階に原因がある可能性が高い。

## v3 の結果の読み方

v3 の結果は、単に pass@k が高いか低いかだけで読まない。

次のように分けて読む。

```text
passed:
  generated.cpp が compile され、test.cpp の assert を通過した。

compile_failed:
  generated.cpp が C++ としてコンパイルできなかった。
  include 不足、namespace 不足、関数シグネチャ不一致、余計な Markdown などが原因になりやすい。

test_failed / run_failed:
  コンパイルはできたが、実行時に assert に失敗した。
  これはアルゴリズム、境界条件、戻り値の解釈が間違っている可能性が高い。

generation_failed:
  Ollama API 呼び出しや生成処理で失敗した。
  これはモデル能力ではなく実行環境側の問題として分けて扱う。
```

例えば、`qwen3-coder:latest` の v3 結果で `vector` が未定義になっている場合、それは主に include または namespace の出力不足である。これは「仕様理解の失敗」というより、「`generated.cpp` 単体でコンパイル可能にする出力制約を守れていない失敗」と読む。

## v4 の目的

`prompt_v4_general_design_self_check` の目的は、v3 で得た汎用設計書を維持したまま、コード生成段階の形式的失敗を減らすことである。

v3 では設計書生成プロンプトを改善する。v4 では設計書生成プロンプトは v3 のまま固定し、コード生成プロンプトに self-check を追加する。

v3 の最終結果では、`gpt-oss:20b` と `phi4:latest` は pass@3 で 10/10 成功した一方、`qwen3-coder:latest` では `problem_000` と `problem_004` が `compile_failed`、`problem_001` が `test_failed` として残った。特に `compile_failed` は、設計書に情報がないというより、後段の codegen prompt が include、namespace、translation unit としての成立条件を十分に守れていない可能性がある。

そのため v4 では design prompt を変更しない。比較上の差分を codegen prompt の self-check に限定する。

つまり、v3 と v4 の比較では、次の差だけを見る。

```text
v3:
  design prompt = prompt_v3_general_design
  codegen prompt = v2相当

v4:
  design prompt = prompt_v3_general_design
  codegen prompt = v2相当 + self-check
```

この設計により、v4 の効果を「コード生成時の自己確認がどれだけ効いたか」として読みやすくする。

v4 の保存先:

```text
experiments/humanevalx_cpp_runs/prompt_v4_general_design_self_check/<model_dir>/
```

## v4 で追加する self-check の内容

v4 の codegen prompt では、最終出力を出す前にモデル内部で次の点を確認させる。

- 設計書に書かれた C++ 関数シグネチャと完全一致しているか。
- 返り値の型を変更していないか。
- 関数名を変更していないか。
- 引数の順序を変更していないか。
- 引数名を変更していないか。
- 引数の型を変更していないか。
- 値渡しを `const reference` に変更していないか。
- reference を値渡しに変更していないか。
- `const` の有無を変更していないか。
- namespace qualification を変更していないか。
- `vector` を使うなら `#include <vector>` があるか。
- シグネチャで `vector<float>` のような非修飾標準ライブラリ型を使う場合、`#include <vector>` だけでなく `using namespace std;` を関数定義前に出しているか。
- `string` を使うなら `#include <string>` があるか。
- `sort` などを使うなら `#include <algorithm>` があるか。
- `abs`, `sqrt`, `pow` などを使うなら `#include <cmath>` があるか。
- `map` を使うなら `#include <map>` があるか。
- `set` を使うなら `#include <set>` があるか。
- `tuple` を使うなら `#include <tuple>` があるか。
- `accumulate` などを使うなら `#include <numeric>` があるか。
- `std::` を使う方針か `using namespace std;` を使う方針かが一貫しているか。
- `generated.cpp` 単体でコンパイルに必要な include が入っているか。
- `test.cpp` 側の include に依存していないか。
- `main` 関数を出していないか。
- テストコードを出していないか。
- Markdown code fence を出していないか。
- 説明文を出していないか。
- C++ コードだけを出しているか。

重要なのは、self-check の内容を出力させないことである。モデルには内部的に確認させ、最終出力は `generated.cpp` に保存できる C++ コードだけにする。

## v4 で期待する改善

v4 で期待する主な改善は、compile_failed の減少である。

特に次の失敗が減ることを期待する。

- `vector` was not declared in this scope
- `string` does not name a type
- `sort` was not declared in this scope
- 関数シグネチャ不一致
- `const reference` 化による test.cpp との不一致
- `std::` と `using namespace std;` の不整合
- Markdown code fence の混入
- 余計な `main` 関数の混入

v4 で compile_failed が減り、pass@k が上がる場合、self-check は形式的なコード生成失敗を抑える効果があったと解釈できる。

一方、compile_failed は減ったが test_failed が増える場合、形式は整ったがアルゴリズム理解はまだ不十分であると解釈する。

初期 v4 の qwen3-coder:latest 小規模検証では、`problem_000` と `problem_004` の compile_failed は include 不足ではなく namespace 不足だった。生成コードには `#include <vector>` があったが、関数シグネチャが `vector<float>` のように非修飾で、`using namespace std;` が出力されていなかった。

このため v4 prompt では、非修飾標準ライブラリ型をシグネチャで維持する場合、include の後、関数定義の前に `using namespace std;` を出力することを self-check に追加する。

## v4 の評価方法

v4 も v3 と同じ条件で評価する。

- 同じ problem set を使う。
- 同じ model set を使う。
- 同じ `temperature` を使う。
- 同じ pass@1 / pass@3 定義を使う。
- 同じ compiler と test.cpp を使う。
- 同じ集計スクリプトを使う。

比較では、少なくとも次を見る。

- v3 pass@1 と v4 pass@1
- v3 pass@3 と v4 pass@3
- v3 compile_failed count と v4 compile_failed count
- v3 sample 単位 pass rate と v4 sample 単位 pass rate
- v3 failure reason と v4 failure reason
- モデル別の改善幅
- 問題別の改善幅

v4 の目的は、v3 よりも高い pass@k を出すことだけではない。失敗原因がどのように変化するかを明確にすることも目的である。

## v3 と v4 の比較で守るべき条件

研究上、比較条件をそろえるために次を守る。

- v3 と v4 で対象問題を変えない。
- v3 と v4 でモデルを変えない。
- v3 と v4 で温度設定を変えない。
- v3 と v4 で `test.cpp` を変えない。
- v3 と v4 で手作業修正を入れない。
- v3 と v4 で設計書生成プロンプトを変えない。
- v4 で変えるのは codegen prompt の self-check だけにする。

この条件を守ることで、v4 の差分を self-check の効果として説明しやすくなる。

## 発表時の説明例

発表では、次の流れで説明すると分かりやすい。

```text
v2 では、関数シグネチャや include に関する制約を強めた結果、少数問題では pass@1 が大きく改善した。

しかし、v2 の設計書生成プロンプトは HumanEval-X のコード形式に最適化されすぎている可能性があった。

そこで v3 では、特定の問題に依存しない一般的な C++ コード読解プロンプトを設計した。
設計書には、関数シグネチャ、引数、返り値、標準ライブラリ依存、include 候補、namespace 方針、値渡しや const/reference、制御構造、境界条件、計算量を含めるようにした。

v3 の目的は、汎用的な設計書生成が後段のコード再生成にどの程度効くかを見ることである。

次の v4 では、設計書生成プロンプトは v3 のまま固定し、コード生成プロンプトに self-check を追加する。
これにより、include 不足、namespace 不足、関数シグネチャ不一致、Markdown 混入などの形式的失敗がどの程度減るかを検証する。
```

## 現時点の注意

v3 はまだ完成版ではない。特に、モデルによっては `generated.cpp` に必要な include や namespace が出ず、compile_failed になるケースが残っている。

そのため、v3 は `Master` にマージする安定版ではなく、`feature/prompt-v3-general-design` 上で検証を続ける実験ブランチとして扱う。

タグ `exp-prompt-v3-general-design` は、その時点の実験環境を再現するための保存点であり、v3 の最終完成を意味するものではない。
