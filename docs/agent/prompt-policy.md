# Prompt Policy

この文書は、CodeEval におけるプロンプトバージョンの管理方針を定義する。

## 目的

プロンプトの内容は、CodeEval における実験条件の一部である。

そのため、プロンプトの変更は明示的に管理し、どの実験でどのプロンプトを使ったかを後から確認できるようにする。

## 参照文書

既存のプロンプトバージョンは、以下に記録する。

- `docs/experiments/prompt_versions.md`

v3 / v4 のプロンプト実験計画は、以下に記録する。

- `docs/experiments/prompt_v3_v4_plan.md`

## 基本ルール

既存のプロンプトバージョンを、説明なしに上書きしてはいけない。

プロンプトの挙動を変更する場合は、新しい明示的なバージョン名を使う。

例：

```text
prompt_v1_baseline
prompt_v2_signature_include
prompt_v3_general_design
prompt_v4_general_design_self_check
```

## v3 のルール

v3 は、設計文書生成プロンプトを改善する実験である。

v3 の目的は、既存 C++ ソースコードから、より一般的で再利用しやすい設計文書を生成することである。

v3 では、以下を行わない。

- 問題ごとの個別チューニング
- モデルごとの特殊プロンプト
- Codex による生成設計文書の手動修正
- Codex による生成 C++ コードの手動修正
- codegen 側の self-check 追加

codegen 側の self-check は v4 の対象とする。

## v4 のルール

v4 は、v3 の設計文書生成プロンプトを固定したうえで、コード生成側に self-check を追加する実験である。

v4 の比較対象は v3 である。

v4 では、以下を見る。

- compile_failed が減るか
- code_generation_failed が減るか
- test_failed がどう変化するか
- pass@1 / pass@3 が改善するか

## 比較ルール

プロンプトバージョンを比較するときは、可能な限り以下の条件を固定する。

- dataset
- selected problems
- model
- temperature
- timeout
- compiler
- number of attempts
- evaluation script
- generated artifact handling

条件が変わった場合は、run summary に明記する。

## 文書更新ルール

プロンプトバージョンを追加・変更した場合は、必要に応じて以下を更新する。

- `docs/experiments/prompt_versions.md`
- `docs/agent/experiment-memory.md`
- `docs/agent/task-log/`

## 禁止事項

以下を行ってはいけない。

- 既存プロンプトを説明なしに上書きする
- 生成設計文書を手動修正して結果を良く見せる
- 生成 C++ コードを手動修正して結果を良く見せる
- v3 と v4 の変更を混ぜたまま比較する
- 不完全な実験結果を完全な結果として報告する
