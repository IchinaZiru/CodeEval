# General Prompt Strategy

## 目的

次の実験では、問題数を単純に増やすことではなく、HumanEval-X C++ 全体に対して同じ単一プロンプトがどこまで安定して機能するかを調べる。

目標は、特定の問題や特定のコードの書き方に過度に依存せず、一般的な C++ の構造、型、標準ライブラリ依存、制御構造、境界条件を読み取れる設計書生成プロンプトを作ることである。

## 対象

- HumanEval-X C++ 全体を対象にする。
- カテゴリ別にプロンプトを分けない。
- 全問題に同じ単一プロンプトを使う。
- 問題カテゴリは、プロンプト切替のためではなく、結果分析のための補助ラベルとして扱う。

## v3 の位置づけ

`prompt_v3_general_design` は、`original.cpp` から `design.md` を作る設計書生成プロンプトを改善する段階である。

```text
original.cpp
  -> prompt_v3_general_design
  -> generated_design/design.md
```

v3 では codegen prompt は v2 相当のまま固定し、設計書生成プロンプトの汎用化が pass@k や設計書品質に与える影響を確認する。

## v3 Design Prompt の方針

設計書には、再実装に必要な情報を仕様として整理させる。

- 対象関数の役割
- C++ 関数シグネチャ
- 引数の型、名前、意味
- 返り値の型と意味
- 値渡し、reference、const の扱い
- namespace qualification の扱い
- 使用している標準ライブラリ型や関数
- 必要な `#include` 候補
- `std::` または `using namespace std;` に関する注意
- 処理手順
- 分岐条件
- ループ構造
- 再帰の有無
- helper 関数や補助構造の有無
- edge case
- 入力制約
- 想定される時間計算量と空間計算量
- 再実装時の注意点

設計書は元コードの丸写しではなく、別の C++ 実装者が同じ仕様を再実装できる粒度の設計書にする。

## pass@k 設計

```text
pass@1:
  1回生成
  temperature = 0.0

pass@3:
  3回生成
  temperature = 0.2
  sample_001, sample_002, sample_003 のうち1つでもテストを通れば成功
```

CSV や JSON では、温度条件を明確にするために `pass@1_temp0.0`、`pass@3_temp0.2` のように記録する。

## pass@k 保存形式

`run_passk_experiment.py` は既存の `run_code_generation.py`、`run_similarity.py`、`run_tests.py` を再利用しつつ、各 sample の成果物を以下に退避する。

```text
experiments/humanevalx_cpp_runs/prompt_v3_general_design/<model>/
  problems/problem_000/
    generated_code/
      generated.cpp
      pass1/
        sample_001/generated.cpp
      pass3/
        sample_001/generated.cpp
        sample_002/generated.cpp
        sample_003/generated.cpp
    results/
      pass1/
        sample_001/
          code_generation_metadata.json
          similarity.json
          test_results.json
          sample_metadata.json
      pass3/
        sample_001/
        sample_002/
        sample_003/
```

既定位置の `generated_code/generated.cpp` と `results/*.json` は、既存スクリプト互換の一時出力として使う。評価に使う永続的な結果は sample 別ディレクトリを見る。

## 実行例

まず dry-run で保存先と実行予定を確認する。

```powershell
python scripts/run_passk_experiment.py `
  --model qwen3-coder:latest `
  --prompt-version prompt_v3_general_design `
  --limit 10 `
  --compiler g++ `
  --continue-on-error `
  --dry-run
```

実験後の pass@k 集計:

```powershell
python scripts/summarize_passk_results.py `
  --run-dir experiments\humanevalx_cpp_runs\prompt_v3_general_design\qwen3-coder_latest
```

`run_passk_experiment.py` は Ollama API を呼び出すため、実験実行前に必ず dry-run で確認する。

## v4 の位置づけ

`prompt_v4_general_design_self_check` は、v3 の設計書生成プロンプトを維持し、codegen prompt に self-check を追加する段階とする。

v4 の self-check では、出力前に以下を内部確認させる。

- 関数シグネチャが設計書と完全一致しているか
- 値渡しを `const reference` に変えていないか
- namespace qualification を変えていないか
- 必要な `#include` が `generated.cpp` に含まれているか
- `main` 関数を含んでいないか
- Markdown code fence を含んでいないか
- 説明文を含んでいないか

ただし、self-check の内容は出力させない。

## 評価

v3 では pass@k だけでなく、設計書品質も評価する。

- pass@1
- pass@3
- compile success rate
- failure reason
- design quality score
- design signature exact match
- include/dependency description
- complexity description

設計書品質と pass@k の関係を見ることで、設計書生成プロンプトの改善がコード再生成成功率にどう影響するかを分析する。
