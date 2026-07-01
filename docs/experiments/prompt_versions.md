# Prompt Versions

詳細な v3/v4 の実験目的、比較条件、評価方法は `docs/experiments/prompt_v3_v4_plan.md` にまとめる。

実行コマンドと集計コマンドは `docs/experiments/run_commands.md` にまとめる。

## prompt_v1_baseline

初期のベースラインプロンプト。

- `original.cpp` から設計書を生成する。
- `generated_design/design.md` から `generated.cpp` を生成する。
- 関数シグネチャや include に関する制約は強くない。

## prompt_v2_signature_include

C++ 再生成で多発していた形式的失敗を抑えるためのプロンプト。

主な強化点:

- 関数シグネチャ完全一致
- 値渡しを `const reference` に変更しない制約
- namespace qualification を勝手に変更しない制約
- `generated.cpp` 単体で必要な `#include` を出す制約
- `test.cpp` の include に依存しない制約
- `main` 関数、テストコード、Markdown code fence、説明文を出さない制約

プロンプト言語は v1 と比較しやすいように日本語ベースを維持する。

## prompt_v3_general_design

HumanEval-X C++ 全体に対して、汎用的な設計書を逆生成するためのプロンプト。

v3 で変更する対象:

- design prompt

v3 で固定する対象:

- codegen prompt は v2 相当を維持する。

目的:

- 特定の問題やコードスタイルに依存しない設計書生成を目指す。
- 一般的な C++ の構造、型、標準ライブラリ依存、制御構造、境界条件を設計書に抽出する。
- 設計書品質と pass@k の関係を評価できるようにする。

設計書に含める情報:

- 対象関数の役割
- 正確な C++ 関数シグネチャ
- 引数と返り値
- 値渡し、reference、const の扱い
- namespace qualification の扱い
- 標準ライブラリ型や関数
- 必要な `#include` 候補
- `std::` または `using namespace std;` に関する注意
- 処理手順、分岐、ループ、再帰、helper の有無
- edge case
- 入力制約
- 時間計算量と空間計算量
- 再実装時の注意点

## prompt_v3_general_design_v2

`prompt_v3_general_design` を上書きせずに追加する、v3.1相当の設計書生成プロンプト。
docs 上では「v3 general design の補強版」として扱う。

v3.1 で変更する対象:

- design prompt

v3.1 で固定する対象:

- codegen prompt は v3 と同じまま維持する。
- codegen self-check は追加しない。

目的:

- v3 の汎用性を維持したまま、再実装に必要な具体性を補う。
- 特定の HumanEval-X 問題だけに過度に適応せず、一般的な C++ 関数の読解観点として使える設計書を生成させる。
- 処理対象、無視条件、状態更新、結果追加タイミング、ループ後処理などを明確にさせる。

追加で設計書に含める情報:

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

実験結果の保存先:

```text
experiments/humanevalx_cpp_runs/prompt_v3_general_design_v2/<model_dir>/
```

## prompt_v4_general_design_self_check

v3 の設計書生成プロンプトを固定し、code generation prompt にだけ self-check を追加するプロンプト。

- design prompt は `prompt_v3_general_design` を維持する。
- codegen prompt は v2 相当を基盤にし、最終出力前の self-check を追加する。
- self-check の内容は出力させず、`generated.cpp` だけを出力させる。

目的:

- 設計書生成を変えずに、コード生成段階の形式的失敗を減らす。
- `generated.cpp` が単体の translation unit としてコンパイルできる確率を上げる。
- include 不足、namespace 不整合、関数シグネチャ不一致、Markdown code fence 混入、余計な `main` 関数混入などを抑える。

v4 で self-check させる内容:

- `generated.cpp` は単体でコンパイル可能か。
- 必要な `#include` があるか。
- `vector` を使うなら `#include <vector>` があるか。
- `string` を使うなら `#include <string>` があるか。
- `map`、`set`、`tuple`、`utility`、`algorithm`、`cmath`、`numeric` などを使うなら対応 include があるか。
- `std::` を使うか `using namespace std;` を使うかが一貫しているか。
- シグネチャで `vector<float>` のような非修飾標準ライブラリ型を使う場合、include だけでなく `using namespace std;` を関数定義前に出しているか。
- 設計書に書かれた C++ 関数シグネチャと完全一致しているか。
- 返り値の型、関数名、引数の順序、引数名、引数の型を変えていないか。
- 値渡しを `const reference` に勝手に変更していないか。
- reference や `const` の有無を変更していないか。
- 余計な `main` 関数、テストコード、Markdown code fence、説明文を出していないか。
- 最終出力が C++ コードのみになっているか。

実験結果の保存先:

```text
experiments/humanevalx_cpp_runs/prompt_v4_general_design_self_check/<model_dir>/
```
