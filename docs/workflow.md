# ワークフロー

## 1. 設計書生成プロンプトを作成

```bash
python scripts/make_design_prompt.py --problem-id problem_000
```

`original.cpp` を元に、ローカル LLM へ渡す `prompts/design_prompt.txt` を生成する。

## 2. ローカル LLM で設計書を生成

`prompts/design_prompt.txt` をローカル LLM に入力し、出力を次の場所に保存する。

```text
experiments/humanevalx_cpp/problems/problem_000/generated_design/design.md
```

## 3. コード生成プロンプトを作成

```bash
python scripts/make_codegen_prompt.py --problem-id problem_000
```

`generated_design/design.md` を元に、ローカル LLM へ渡す `prompts/codegen_prompt.txt` を生成する。

## 4. ローカル LLM で C++ コードを生成

`prompts/codegen_prompt.txt` をローカル LLM に入力し、出力を次の場所に保存する。

```text
experiments/humanevalx_cpp/problems/problem_000/generated_code/generated.cpp
```

## 5. 類似度を計算

```bash
python scripts/run_similarity.py --problem-id problem_000
```

結果は `results/similarity.json` に保存される。

## 6. テストを実行

```bash
python scripts/run_tests.py --problem-id problem_000 --compiler g++
```

C++ コンパイラが PATH にない場合は、`--compiler` に利用可能なコンパイラのパスを指定する。

## 7. 結果を集約

```bash
python scripts/summarize_results.py
```

`experiments/humanevalx_cpp/summary/` 以下に CSV と Markdown レポートが出力される。

## 複数問題を一括実行

```bash
python scripts/run_pipeline.py --problem-ids problem_000 problem_001 problem_002 problem_003 problem_004 --model qwen2.5-coder:7b --temperature 0 --compiler g++
```

`--continue-on-error` を指定すると、1 問で失敗しても次の問題に進む。
