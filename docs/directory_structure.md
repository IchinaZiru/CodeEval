# ディレクトリ構成

このリポジトリでは、実験対象データ、プロンプト、ローカル LLM の出力、評価結果を分けて管理する。

## 主要ディレクトリ

- `data/raw/`: 将来 HumanEval-X 本体を配置する場所。
- `data/selected/`: 実験対象に選んだ問題 ID を管理する場所。
- `scripts/`: プロンプト作成、評価、集約のための Python スクリプト。
- `experiments/humanevalx_cpp/problems/`: 問題ごとの入力、プロンプト、生成物、結果を置く場所。
- `experiments/humanevalx_cpp/summary/`: 複数問題の結果を集約した CSV とレポートを置く場所。
- `docs/`: 実験設計、構成、ワークフローの説明。

## problem_000

`problem_000` は最小パイプライン確認用のダミー問題である。

- `spec.md`: 問題仕様。
- `original.cpp`: 正解実装。
- `test.cpp`: 生成コードを検証する assert テスト。
- `prompts/`: ローカル LLM に渡すプロンプト。
- `generated_design/`: ローカル LLM が生成した設計書の保存先。
- `generated_code/`: ローカル LLM が生成した C++ コードの保存先。
- `results/`: 類似度計算やテスト実行の結果 JSON。
