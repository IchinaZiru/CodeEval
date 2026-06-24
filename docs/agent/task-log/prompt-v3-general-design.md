# Task Log: prompt_v3_general_design

この文書は、v3 の一般設計文書生成プロンプトに関する作業ログである。

## 目的

v3 の目的は、既存 C++ ソースコードから、より一般的で再利用しやすい設計文書を生成することである。

v3 では、設計文書生成プロンプトを改善する。

## v3 で行うこと

- 設計文書生成プロンプトを一般化する
- 対象関数の目的、入力、出力、制約、アルゴリズム方針を明確に含める
- 後段の C++ コード生成が使いやすい設計文書を目指す
- プロンプトバージョンを明示的に管理する
- 実験条件を記録する

## v3 で行わないこと

- 問題ごとの個別チューニング
- モデルごとの特殊プロンプト
- Codex による生成設計文書の手動修正
- Codex による生成 C++ コードの手動修正
- codegen 側の self-check 追加

## 実装時の注意

v3 実装前に、Codex は以下を読む。

- `AGENTS.md`
- `docs/agent/index.md`
- `docs/agent/prompt-policy.md`
- `docs/agent/evaluation-policy.md`
- `docs/experiments/prompt_versions.md`
- `docs/experiments/prompt_v3_v4_plan.md`

## 記録欄

### 実装メモ

未記入。

### 実験メモ

未記入。

### 気づき

未記入。
