# CodeEval Agent Knowledge Index

このディレクトリは、CodeEval に関する永続的な研究メモと、Codex などのAIエージェント向け作業ルールを管理する場所である。

## 目的

この `docs/agent/` ディレクトリの目的は、CodeEval の研究方針、実験条件、プロンプト管理ルール、評価方針を、チャット単位で失われない形で保存することである。

Codex のチャットは毎回文脈が分断されるため、重要な前提をリポジトリ内の Markdown 文書として残す。

## このディレクトリの使い方

Codex に研究関連の実装や修正を依頼する前に、まず以下の文書を読ませる。

1. `AGENTS.md`
2. `docs/agent/index.md`
3. `docs/agent/codex-operating-rules.md`
4. `docs/agent/prompt-policy.md`
5. `docs/agent/evaluation-policy.md`
6. `docs/agent/failure-taxonomy.md`
7. `docs/agent/experiment-memory.md`
8. `docs/experiments/prompt_versions.md`
9. `docs/experiments/prompt_v3_v4_plan.md`

## ディレクトリ構成

```text
docs/agent/
├── index.md
├── codex-operating-rules.md
├── prompt-policy.md
├── evaluation-policy.md
├── failure-taxonomy.md
├── experiment-memory.md
├── task-log/
└── run-summaries/
```

## 各ファイルの役割

### `index.md`

このファイルである。

`docs/agent/` 全体の目的と読み順を説明する。

### `codex-operating-rules.md`

Codex が編集してよいもの、編集してはいけないもの、作業前に確認すべきことを定義する。

### `prompt-policy.md`

プロンプトバージョンの管理方針を定義する。

v1、v2、v3、v4 のようなプロンプト差分を、実験条件として明示的に扱うための文書である。

### `evaluation-policy.md`

実験結果をどのように評価・記録・比較するかを定義する。

pass@1、pass@3、compile success、test success、failure distribution などの扱いを整理する。

### `failure-taxonomy.md`

実験失敗を分類するための文書である。

`pipeline_failed`、`design_generation_failed`、`code_generation_failed`、`compile_failed`、`test_failed`、`passed` などの区別を明確にする。

### `experiment-memory.md`

研究の重要な決定、過去の方針、今後の注意点を蓄積する文書である。

Codex に長期的な研究文脈を渡すための中心的なメモとして使う。

### `task-log/`

作業単位の記録を置く場所である。

例：

- v3 実装作業ログ
- v4 self-check 実装作業ログ
- 評価スクリプト修正ログ

### `run-summaries/`

実験実行後の人間向け要約を置く場所である。

生成された生ログやCSVではなく、実験の条件、結果、気づきをまとめた Markdown を置く。

## 重要な原則

Codex は、研究基盤の実装・整理・文書化を支援する。

しかし、Codex は、評価対象であるローカルLLMの代わりに設計文書やC++コードを手動生成してはいけない。

CodeEval では、以下を明確に分離する。

- Codex が整備するもの
- ローカルLLMが生成するもの
- 実験によって記録されるもの
- 人間が研究メモとして解釈するもの

この分離を崩すと、実験結果の信頼性が下がる。
