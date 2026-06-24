# Task Log: prompt_v4_general_design_self_check

この文書は、v4 のコード生成 self-check に関する作業ログである。

## 目的

v4 の目的は、v3 の設計文書生成プロンプトを固定したうえで、コード生成側に self-check を追加し、再生成 C++ コードの品質が改善するかを評価することである。

## v4 で行うこと

- v3 の設計文書生成プロンプトを固定する
- コード生成プロンプトに self-check を追加する
- 出力が C++ コードのみになるよう制約する
- 関数シグネチャ、include、namespace、返り値、コンパイル可能性などを確認させる
- v3 と比較して failure distribution がどう変わるかを見る

## v4 で行わないこと

- v3 の設計文書生成プロンプトを同時に変更する
- 問題ごとの個別チューニング
- Codex による生成設計文書の手動修正
- Codex による生成 C++ コードの手動修正
- 失敗結果の削除や補完

## 比較で見ること

v4 では、特に以下を見る。

- `compile_failed` が減るか
- `code_generation_failed` が減るか
- `test_failed` が増減するか
- `passed` が増えるか
- pass@1 / pass@3 が改善するか

## 解釈の注意

`compile_failed` が減って `test_failed` が増えた場合、self-check によって構文的には有効なコードが増えたが、意味的な正しさはまだ不足している可能性がある。

この場合、単純に「悪化」とは限らず、失敗の段階が変化したと解釈する。

## 実装時の注意

v4 実装前に、Codex は以下を読む。

- `AGENTS.md`
- `docs/agent/index.md`
- `docs/agent/prompt-policy.md`
- `docs/agent/evaluation-policy.md`
- `docs/agent/failure-taxonomy.md`
- `docs/experiments/prompt_versions.md`
- `docs/experiments/prompt_v3_v4_plan.md`

## 記録欄

### 実装メモ

未記入。

### 実験メモ

未記入。

### 気づき

未記入。
