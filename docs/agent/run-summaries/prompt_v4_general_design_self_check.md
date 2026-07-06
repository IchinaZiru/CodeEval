# prompt_v4_general_design_self_check 実験結果まとめ

## 実験条件

- prompt version: prompt_v4_general_design_self_check
- 対象: HumanEval-X C++ 先頭10問
- design prompt: prompt_v3_general_design と同一
- codegen prompt: v2相当 + self-check
- design temperature: 0.0
- pass@1 temperature: 0.0
- pass@3 temperature: 0.2
- pass@3 samples: 3

## v4 結果

| model | pass@1 | pass@3 | pass@3 sample単位 |
|---|---:|---:|---:|
| gpt-oss:20b | 10/10 | 10/10 | 30/30 |
| phi4:latest | 10/10 | 10/10 | 30/30 |
| qwen3-coder:latest | 7/10 | 7/10 | 21/30 |

## v3 との比較

| model | v3 pass@1 | v4 pass@1 | v3 pass@3 | v4 pass@3 | v3 pass@3 sample単位 | v4 pass@3 sample単位 |
|---|---:|---:|---:|---:|---:|---:|
| gpt-oss:20b | 9/10 | 10/10 | 10/10 | 10/10 | 30/30 | 30/30 |
| phi4:latest | 10/10 | 10/10 | 10/10 | 10/10 | 30/30 | 30/30 |
| qwen3-coder:latest | 7/10 | 7/10 | 7/10 | 7/10 | 21/30 | 21/30 |

## qwen3-coder:latest の失敗問題

v4 での qwen3-coder:latest の失敗問題は以下である。

| problem | status |
|---|---|
| problem_000 | compile_failed |
| problem_001 | test_failed |
| problem_009 | test_failed |

参考として、v3 での qwen3-coder:latest の失敗問題は以下であった。

| problem | status |
|---|---|
| problem_000 | compile_failed |
| problem_001 | test_failed |
| problem_004 | compile_failed |

## v4 で改善した点

v4 では、v3 の design prompt を固定し、codegen prompt に self-check を追加した。

結果として、gpt-oss:20b は pass@1 が v3 の 9/10 から v4 では 10/10 に改善した。pass@3 と pass@3 sample単位は v3 と同じく 10/10、30/30 を維持した。

phi4:latest は v3 と v4 の両方で pass@1、pass@3、pass@3 sample単位がすべて最大値であり、v4 でも性能低下は見られなかった。

qwen3-coder:latest では総合成績は変わらなかったが、v3 で compile_failed だった problem_004 は v4 で passed になった。この点では、self-check が namespace 不足などの形式的失敗を一部改善できた可能性がある。

## v4 で改善しなかった点

qwen3-coder:latest の pass@1 と pass@3 は、v3 と v4 のどちらも 7/10 であり、総合的な pass rate は改善しなかった。

また、v4 でも problem_000 は compile_failed のまま残った。self-check 指示を追加しても、qwen3-coder:latest では namespace 問題が完全には解消されなかった。

さらに、v3 では失敗していなかった problem_009 が v4 では test_failed になった。problem_004 の改善と入れ替わる形で problem_009 が失敗しており、self-check は総合成績を必ず改善するとは限らない。

## self-check の効果と限界

v4 の self-check は、コード生成段階で次のような形式的失敗を抑えることを目的としていた。

- include不足
- namespace不足
- 関数シグネチャ不一致
- Markdown code fence 混入
- main関数の混入
- test code の混入
- generated.cpp が単体の translation unit として成立しない問題

実験結果から、self-check は一部の形式的失敗には効果がある可能性がある。特に gpt-oss:20b の pass@1 改善と、qwen3-coder:latest の problem_004 改善は、codegen prompt 側の制約強化が有効だった可能性を示している。

一方で、LLM に自己確認を指示するだけでは、include、namespace、signature などの形式的制約を完全には守れない。qwen3-coder:latest では problem_000 の namespace 問題が v4 でも残っており、モデルが self-check 指示を常に実行・反映するとは限らないことが確認された。

また、self-check によって形式面の注意を増やしても、アルゴリズムや境界条件の解釈が改善するとは限らない。problem_001 と problem_009 の test_failed は、compile 可能なコードであっても、テストが要求する振る舞いを満たせない場合が残ることを示している。

## 次の方針

次は、単純に v5 としてプロンプトをさらに強くするのではなく、生成後の静的検査・失敗分類を強化する方向が妥当である。

理由は以下である。

- v4 で self-check を追加しても、qwen3-coder:latest は problem_000 の namespace 問題を解消できなかった。
- LLM に自己確認させるだけでは、include、namespace、signature などの形式的制約を完全には守れない。
- そのため、生成後に外部スクリプトで形式的失敗を検出し、失敗原因をより細かく分類する必要がある。

次に検出したい項目:

- include不足
- namespace不足
- 関数シグネチャ不一致
- Markdown code fence 混入
- main関数の混入
- test code の混入
- generated.cpp が単体の translation unit として成立しているか

この静的検査は、生成コードを手修正するための機能ではない。あくまで、生成結果を評価し、失敗原因を細かく分類するための評価機能として位置づける。
