# prompt_v3_general_design 実験結果まとめ

## 実験条件

- prompt version: prompt_v3_general_design
- 対象: HumanEval-X C++ 先頭10問
- design temperature: 0.0
- pass@1 temperature: 0.0
- pass@3 temperature: 0.2
- pass@3 samples: 3

## 結果

| model | pass@1 | pass@3 | pass@3 sample単位 |
|---|---:|---:|---:|
| gpt-oss:20b | 9/10 | 10/10 | 30/30 |
| phi4:latest | 10/10 | 10/10 | 30/30 |
| qwen3-coder:latest | 7/10 | 7/10 | 21/30 |

## qwen3-coder:latest の失敗問題

| problem | status |
|---|---|
| problem_000 | compile_failed |
| problem_001 | test_failed |
| problem_004 | compile_failed |

## 考察

prompt_v3_general_design では、設計書生成プロンプトをより汎用的なC++コード読解向けに改善した。

結果として、gpt-oss:20b は pass@1 で 9/10、pass@3 で 10/10、phi4:latest は pass@1/pass@3 ともに 10/10 となった。
また、qwen3-coder:latest も pass@1/pass@3 ともに 7/10 となり、以前の結果より改善した。

qwen3-coder:latest の失敗3問のうち、2問は compile_failed、1問は test_failed であった。
compile_failed は、設計書に情報が不足しているというより、後段の codegen prompt が include、namespace、関数シグネチャ、出力形式などを十分に守れていない可能性が高い。

そのため、次の改善では v3 の design prompt は固定し、codegen prompt に self-check を追加する prompt_v4_general_design_self_check に進むのが妥当である。

## 次の方針

prompt_v4_general_design_self_check では、以下の条件で比較する。

- design prompt = prompt_v3_general_design のまま固定
- codegen prompt = v2相当 + self-check
- 目的 = include不足、namespace不整合、signature不一致、Markdown混入などの形式的失敗を減らす

特に、qwen3-coder:latest の compile_failed 2問を改善できるかを確認する。
