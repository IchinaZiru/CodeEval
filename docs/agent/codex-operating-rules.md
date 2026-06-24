# Codex Operating Rules

この文書は、CodeEval リポジトリにおける Codex の作業ルールを定義する。

## 基本原則

Codex は、実装・保守・文書化を支援するAIエージェントである。

Codex は、研究対象であるローカルLLMの役割を代替してはいけない。

CodeEval の研究対象は、ローカルLLMが既存 C++ ソースコードを読み、設計文書を生成し、その設計文書から C++ コードを再生成できるかである。

そのため、Codex が生成物を手で直してしまうと、実験条件が崩れる。

## Codex が編集してよいもの

Codex は、以下を編集してよい。

- `scripts/` 以下の Python スクリプト
- プロンプトテンプレート生成コード
- 実験実行・評価・集計用のスクリプト
- `docs/` 以下の説明文書
- `README.md`
- 再現性を高めるための補助ツール
- リポジトリ構成の整理

## Codex が研究結果として手動編集してはいけないもの

Codex は、以下を研究結果として手動作成・手動修正してはいけない。

- 生成された設計文書
- 生成された C++ ソースコード
- ローカルLLMの出力ファイル
- HumanEval-X の raw JSONL ファイル
- 実験結果の JSON / CSV ファイル
- pass / fail の集計結果

これらが壊れている場合、Codex は生成物を直接直すのではなく、生成するためのスクリプト、プロンプト、実験条件を改善する。

## 作業前に行うこと

研究関連の変更を行う前に、Codex は次を行う。

1. `AGENTS.md` を読む
2. `docs/agent/index.md` を読む
3. 関連する `docs/agent/` 内の方針文書を読む
4. 関連する `docs/experiments/` 内の実験文書を読む
5. 変更前に、理解した内容を短く要約する

## ブランチ運用

v3 / v4 のプロンプト実験作業は、以下のブランチを基準とする。

- `feature/prompt-v3-general-design`

Obsidian / Codex 用の知識管理文書は、以下のブランチで整備する。

- `docs/obsidian-agent-knowledge`

この文書管理ブランチでは、不要なプロンプト実装変更を混ぜない。

## プロンプト変更ルール

Codex は、既存のプロンプトバージョンを説明なしに上書きしてはいけない。

プロンプト挙動を変更する場合は、以下を行う。

1. 明示的なプロンプトバージョン名を使う
2. そのバージョンの目的を文書化する
3. 前バージョンとの差分を説明する
4. 比較条件を保つ
5. 関連するドキュメントを更新する

## 実験実行ルール

長い実験を実行する前に、dry-run または小規模実行を優先する。

Codex は、実験結果を推測で作ってはいけない。

失敗した場合は、次の区別を保って記録する。

- pipeline failure
- design generation failure
- code generation failure
- compile failure
- test failure
- pass

## 文書化ルール

研究ロジックや実験条件を変更した場合、将来のチャットでも理由が分かるように文書を更新する。

重要な決定は、以下に記録する。

- `docs/agent/experiment-memory.md`
- `docs/agent/task-log/`
- `docs/experiments/`

## 安全ルール

private notes、Obsidian設定、raw dataset、生成実験結果を不用意に commit してはいけない。

変更ファイルを確認せずに `git add .` を使わない。
