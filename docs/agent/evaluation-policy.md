# Evaluation Policy

この文書は、CodeEval の実験結果をどのように評価・記録・報告するかを定義する。

## 目的

評価結果は、研究上の根拠である。

そのため、再現可能であり、実験条件が明確であり、手動修正によって歪められていない必要がある。

## 評価対象

CodeEval では、ローカルLLMが以下の流れをどれだけ成功できるかを評価する。

1. 既存 C++ ソースコードを読む
2. 設計文書を生成する
3. 設計文書から C++ コードを再生成する
4. 再生成コードがテストを通過するか確認する

## 主な評価指標

主な評価指標は以下である。

- pass@1
- pass@k 形式の指標、特に pass@3
- compile success rate
- test success rate
- failure status distribution

## 比較ルール

プロンプトバージョンやモデルを比較するときは、可能な限り以下を固定する。

- dataset
- selected problems
- model
- temperature
- timeout
- number of attempts
- compiler
- test runner
- evaluation scripts

条件が変わった場合は、必ず run summary に記録する。

## v3 の評価

v3 では、より一般的な設計文書生成プロンプトが、後段のコード再生成にどのような影響を与えるかを評価する。

v3 には、codegen 側の self-check 改善を含めない。

## v4 の評価

v4 では、v3 の設計文書生成プロンプトを固定する。

そのうえで、codegen 側に self-check を追加し、compile success、test success、pass@k 形式の結果が改善するかを評価する。

## 報告ルール

不完全な実験を、完全な結果として報告してはいけない。

実験が不完全な場合は、以下を記録する。

- model name
- prompt version
- dataset または problem range
- 実行コマンド
- 失敗した段階
- 観察されたエラー
- 結果から除外するのか、失敗として扱うのか

## 禁止事項

以下を行ってはいけない。

- 評価前に生成 C++ コードを手動修正する
- 評価前に生成設計文書を手動修正する
- 失敗結果を削除して成功率を良く見せる
- 条件が異なる結果を、同一条件の結果として混ぜる
- 未実行の結果を推測で補完する

## Run Summary の保存場所

人間が読むための実験要約は、以下に保存する。

- `docs/agent/run-summaries/`

生成された生ログ、CSV、JSON などの実験出力は、設定された実験出力ディレクトリに保存し、原則として commit しない。
