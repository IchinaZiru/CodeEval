# Run Summaries

このディレクトリには、人間が読むための実験要約を保存する。

ここには、生の実験ログや生成された CSV / JSON ではなく、実験条件、結果、観察、解釈をまとめた Markdown を置く。

## 記録する内容

各 run summary には、可能な限り以下を記録する。

- 実行日
- branch
- model
- prompt version
- dataset / problem range
- temperature
- timeout
- number of attempts
- command
- 主な結果
- failure distribution
- 気づき
- 次に確認すること

## 注意

生成された実験出力そのものは、原則として Git に commit しない。

このディレクトリには、人間が整理した要約のみを置く。
