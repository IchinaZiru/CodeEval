# AGENTS.md

## プロジェクト概要

このリポジトリは CodeEval である。

CodeEval は、ローカルLLMによるリバースエンジニアリング支援能力を評価するための研究パイプラインである。

基本的な流れは以下の通りである。

1. 既存の C++ ソースコードを入力する
2. ローカルLLMに設計文書を生成させる
3. 生成された設計文書をもとに、ローカルLLMに C++ コードを再生成させる
4. 再生成された C++ コードをテストし、pass@k 形式の指標などで評価する

## Codex の役割

Codex は、この研究の実装・保守を支援するために使用する。

Codex が編集してよいものは以下である。

- Python スクリプト
- プロンプトテンプレート生成コード
- 実験実行用スクリプト
- 評価・集計用スクリプト
- README
- docs 以下の説明文書
- リポジトリ構成の整理

ただし、Codex は、研究対象であるローカルLLMの役割を代替してはいけない。

## Codex が手動作成・手動修正してはいけないもの

Codex は、以下を研究結果として直接作成・修正してはいけない。

- 生成された設計文書
- 生成された C++ コード
- ローカルLLMの出力ファイル
- HumanEval-X の raw JSONL ファイル
- 実験結果の JSON / CSV ファイル
- pass / fail の集計結果

これらが壊れている場合、Codex は生成物そのものを手で直すのではなく、生成するためのスクリプト、プロンプト、実験条件を改善する。

## 必ず読む文書

研究関連の作業を始める前に、Codex は以下を読む。

- `docs/agent/index.md`
- `docs/agent/codex-operating-rules.md`
- `docs/agent/prompt-policy.md`
- `docs/agent/evaluation-policy.md`
- `docs/agent/failure-taxonomy.md`
- `docs/agent/experiment-memory.md`
- `docs/experiments/prompt_versions.md`
- `docs/experiments/prompt_v3_v4_plan.md`

## 重要ブランチ

v3 / v4 のプロンプト実験計画は、以下のブランチを基準とする。

- `feature/prompt-v3-general-design`

Obsidian / Codex 用の知識管理文書は、以下のブランチで整備する。

- `docs/obsidian-agent-knowledge`

## プロンプトバージョンのルール

既存のプロンプト挙動を、説明なしに上書きしてはいけない。

プロンプトの挙動を変更する場合は、以下を守る。

1. 明示的なプロンプトバージョン名を使う
2. 前バージョンとの差分を文書化する
3. 比較条件を明確にする
4. 関連する docs を更新する

## 実験の安全ルール

長い実験を実行する前に、できるだけ dry-run や小規模実行で確認する。

raw dataset や生成物、ローカル実験結果を不用意に commit してはいけない。

実験結果を推測で補完してはいけない。

失敗・未実行・不完全な結果は、その事実を明記する。