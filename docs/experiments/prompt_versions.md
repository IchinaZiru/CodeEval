# Prompt Versions

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

## prompt_v4_general_design_self_check

予定している次段階のプロンプト。

- design prompt は `prompt_v3_general_design` を維持する。
- codegen prompt に self-check を追加する。
- self-check の内容は出力させず、`generated.cpp` だけを出力させる。
