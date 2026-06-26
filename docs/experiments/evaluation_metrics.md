# Evaluation Metrics

This document defines the evaluation metrics used for HumanEval-X C++ regeneration experiments.

## 主指標

### test pass rate

`generated.cpp + test.cpp` がコンパイル・実行され、assert テストを通過した割合を主指標とする。

## 実行ステータス系補助指標

- `compile_failed`: C++ コンパイルに失敗した問題数
- `test_failed`: コンパイル後の実行または assert に失敗した問題数
- `timeout`: コンパイル、実行、または外部処理がタイムアウトした問題数
- `generation_failed`: 生成段階で失敗した問題数
- `missing_generated_code`: `generated_code/generated.cpp` が存在しない問題数

これらは pass rate の内訳を説明するための補助指標である。

## テキスト類似度

- `text_similarity`: `difflib.SequenceMatcher` による文字列類似度
- `normalized_edit_similarity`: 編集距離に近い正規化類似度。現時点では外部依存を避けるため `SequenceMatcher` を流用する

## トークン類似度

- `token_jaccard_similarity`: 簡易 C++ token 集合の Jaccard 類似度
- `token_cosine_similarity`: 簡易 C++ token 出現頻度ベクトルの cosine 類似度

トークナイズは厳密な C++ parser ではなく、コメント除去、文字列リテラル簡略化、識別子・数値・演算子・括弧類の抽出による補助指標である。

## 構造系補助指標

- `line_count_ratio`: 生成コード行数 / 元コード行数
- `brace_depth_diff`: 生成コード最大 brace depth - 元コード最大 brace depth
- `signature_exact_match`: 空白を正規化した関数シグネチャが一致するか
- `include_likely_complete`: 使用している標準ライブラリ要素に対して `#include` が足りていそうか

`signature_exact_match` と `include_likely_complete` は簡易正規表現ベースの補助判定であり、完全な静的解析ではない。

## Dolos

Dolos は、`original.cpp` と `generated.cpp` の構造的・トークン的類似度を補助的に見るための外部指標として扱う。

本リポジトリでは、まず以下だけを提供する。

- Dolos 入力用の `dolos_inputs/` エクスポート
- `dolos_pairs.csv` による対応表
- 汎用 CSV 形式の Dolos 結果取り込み

想定する取り込み CSV:

```csv
problem_id,dolos_similarity,dolos_notes
problem_000,0.91,
problem_001,0.75,
```

## 設計書品質

`generated_design/design.md` に対して、以下をキーワードベースで判定する。

- signature block
- input description
- output description
- algorithm description
- edge case description
- constraints description
- standard library dependency description
- required include description
- namespace policy description
- value/reference/const description
- complexity description
- design signature exact match
- return value mention
- parameter mention
- design quality score

`design_quality_score` は boolean 判定項目の平均で、0 から 1 の範囲に正規化する。

## 解釈例

- passed かつ similarity 高: 元実装に近い形で再生成できた可能性
- passed かつ similarity 低: 元実装とは異なるが機能的に正しい別実装を生成できた可能性
- failed かつ similarity 高: 構造は似ているが、境界条件や細部に誤りがある可能性
- failed かつ similarity 低: 設計書理解またはコード再生成が大きく崩れた可能性
- design_quality_score 高だが test_failed: 設計書は十分でも、モデルの実装能力や細部推論に問題がある可能性
- design_quality_score 低だが passed: 問題が単純、またはモデルの事前知識・推論能力で補完できた可能性

## 生成される集計ファイル

単一 run:

```text
<run-dir>/summary/test_summary.csv
<run-dir>/summary/combined_summary.csv
<run-dir>/summary/summary_metrics.json
```

複数モデル:

```text
experiments/humanevalx_cpp_runs/<prompt_version>/summary/model_summary.csv
experiments/humanevalx_cpp_runs/<prompt_version>/summary/model_summary.md
experiments/humanevalx_cpp_runs/<prompt_version>/summary/problem_results.csv
```

Dolos:

```text
<run-dir>/dolos_inputs/
<run-dir>/dolos_inputs/dolos_pairs.csv
<run-dir>/summary/combined_summary_with_dolos.csv
```
