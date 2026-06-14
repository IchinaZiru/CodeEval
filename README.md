# HumanEval-X C++ Regeneration Experiment

このリポジトリは、HumanEval-X の C++ 問題を対象に、正解ソースコードから設計書を逆生成し、その設計書から C++ コードを再生成して評価するための研究用パイプラインです。

現時点では HumanEval-X 本体の取り込みや本格評価は行いません。まずはダミー問題 `problem_000`〜`problem_004` で、フォルダ構成、プロンプト生成、類似度計算、テスト実行、結果集約の小規模フローを確認します。

## 役割分担

Codex はこのリポジトリの環境構築、ディレクトリ構成、スクリプト雛形、README とドキュメントの整備だけを担当します。

実験用の設計書や C++ 生成コードは Codex が作成しません。生成は、ユーザーがローカル環境で動かす LLM によって行います。

ローカル LLM の出力先は以下に固定します。

- 設計書: `experiments/humanevalx_cpp/problems/problem_000/generated_design/design.md`
- 生成コード: `experiments/humanevalx_cpp/problems/problem_000/generated_code/generated.cpp`

## HumanEval-X C++ を使う理由

HumanEval-X は、多言語コード生成能力を比較するためのベンチマークです。C++ 問題を対象にすることで、関数シグネチャ、型、境界条件、テスト通過率を比較しやすく、設計書を介したコード再生成が元の正解実装にどの程度近づくかを調べられます。

## ディレクトリ構成

```text
.
├── README.md
├── requirements.txt
├── scripts/
│   ├── prepare_dataset.py
│   ├── make_design_prompt.py
│   ├── make_codegen_prompt.py
│   ├── ollama_client.py
│   ├── run_design_generation.py
│   ├── run_code_generation.py
│   ├── run_pipeline.py
│   ├── run_similarity.py
│   ├── run_tests.py
│   └── summarize_results.py
├── data/
│   ├── raw/
│   └── selected/
│       └── selected_ids.txt
├── experiments/
│   └── humanevalx_cpp/
│       ├── problems/
│       │   ├── problem_000/
│       │       ├── spec.md
│       │       ├── original.cpp
│       │       ├── test.cpp
│       │       ├── prompts/
│       │       │   ├── design_prompt.txt
│       │       │   └── codegen_prompt.txt
│       │       ├── generated_design/
│       │       ├── generated_code/
│       │       └── results/
│       │   ├── problem_001/
│       │   ├── problem_002/
│       │   ├── problem_003/
│       │   └── problem_004/
│       └── summary/
│           ├── similarity_results.csv
│           ├── test_results.csv
│           ├── summary_metrics.json
│           └── report.md
└── docs/
    ├── experiment_design.md
    ├── directory_structure.md
    └── workflow.md
```

## ダミー問題での使い方

Python 3.10 以降を想定しています。現時点の Python スクリプトは標準ライブラリのみで動作します。

### 1. 設計書生成用プロンプトを作る

```bash
python scripts/make_design_prompt.py --problem-id problem_000
```

生成された `experiments/humanevalx_cpp/problems/problem_000/prompts/design_prompt.txt` をローカル LLM に入力します。

生成される設計書には、関数名、C++ の関数シグネチャ、引数名と型、返り値の型と意味、処理内容、境界条件、想定される計算量を必ず含める方針です。特に C++ の関数シグネチャは、後続のコード生成で関数名・引数・戻り値を間違えないよう、Markdown の `cpp` コードブロックで明記させます。

### 2. ローカル LLM の設計書出力を保存する

ローカル LLM が出力した設計書を、次のパスに保存します。

```text
experiments/humanevalx_cpp/problems/problem_000/generated_design/design.md
```

### 3. コード生成用プロンプトを作る

```bash
python scripts/make_codegen_prompt.py --problem-id problem_000
```

生成された `experiments/humanevalx_cpp/problems/problem_000/prompts/codegen_prompt.txt` をローカル LLM に入力します。

### 4. ローカル LLM の C++ 出力を保存する

ローカル LLM が出力した C++ 実装を、次のパスに保存します。

```text
experiments/humanevalx_cpp/problems/problem_000/generated_code/generated.cpp
```

`generated.cpp` は `int add(int a, int b)` の実装だけを含め、`main` やテストコードは含めない想定です。

### 5. 元コードとの類似度を計算する

```bash
python scripts/run_similarity.py --problem-id problem_000
```

結果は `experiments/humanevalx_cpp/problems/problem_000/results/similarity.json` に保存されます。

### 6. 生成コードをテストする

```bash
python scripts/run_tests.py --problem-id problem_000 --compiler g++
```

`run_tests.py` は `generated_code/generated.cpp` と `test.cpp` を一緒にコンパイルし、生成された実行ファイルを走らせる雛形です。C++ コンパイラは別途インストールしてください。この環境では `g++`、`clang++`、`cl` が PATH にないため、実行時には `--compiler` で利用可能なコンパイラ名またはパスを指定します。

テスト結果は `experiments/humanevalx_cpp/problems/problem_000/results/test_results.json` に保存されます。

### 7. 結果を集約する

```bash
python scripts/summarize_results.py
```

集約結果は `experiments/humanevalx_cpp/summary/` 以下に出力されます。

## Ollama API を使う場合

Ollama がローカルで起動しており、HTTP API `http://localhost:11434` にアクセスできる前提です。モデル名は環境によって異なるため、必ず `--model` で指定します。生成結果の再現性を高めるため、`--temperature` は指定可能で、初期値は `0` です。

Codex は設計書や C++ コードを直接生成しません。以下のスクリプトは、プロンプトを Ollama API に送り、ローカル LLM の出力を所定の場所へ保存します。

### 1. 設計書を Ollama で生成する

必要に応じて設計書生成用プロンプトを更新します。

```bash
python scripts/make_design_prompt.py --problem-id problem_000
```

その後、Ollama API 経由で設計書を生成します。

```bash
python scripts/run_design_generation.py --problem-id problem_000 --model qwen2.5-coder:7b --temperature 0
```

この設計書生成プロンプトは、後続の `run_code_generation.py` が参照するため、設計書内に C++ の関数シグネチャを `cpp` コードブロックで含めるよう指示します。

出力先:

```text
experiments/humanevalx_cpp/problems/problem_000/generated_design/design.md
```

生成メタデータ:

```text
experiments/humanevalx_cpp/problems/problem_000/results/design_generation_metadata.json
```

Ollama の URL を変更する場合は `--ollama-url` を指定します。

```bash
python scripts/run_design_generation.py --problem-id problem_000 --model qwen2.5-coder:7b --temperature 0 --ollama-url http://localhost:11434
```

### 2. C++ コードを Ollama で生成する

`run_code_generation.py` は `generated_design/design.md` を読み、`prompts/codegen_prompt.txt` を作成または更新してから Ollama API に送信します。

```bash
python scripts/run_code_generation.py --problem-id problem_000 --model qwen2.5-coder:7b --temperature 0
```

出力先:

```text
experiments/humanevalx_cpp/problems/problem_000/generated_code/generated.cpp
```

生成メタデータ:

```text
experiments/humanevalx_cpp/problems/problem_000/results/code_generation_metadata.json
```

モデルが Markdown のコードフェンス、たとえば ```` ```cpp ```` を含む応答を返した場合、保存時にはフェンス内部の C++ コードだけを抽出します。

### 3. 類似度とテストを実行する

```bash
python scripts/run_similarity.py --problem-id problem_000
python scripts/run_tests.py --problem-id problem_000 --compiler g++
python scripts/summarize_results.py
```

`run_tests.py` を使うには C++ コンパイラが必要です。`g++` 以外を使う場合は `--compiler` に利用可能なコンパイラ名またはパスを指定します。

## 複数問題を一括実行する

現在は HumanEval-X 本体ではなく、以下の小規模ダミー問題でパイプラインを安定化します。

- `problem_000`: `add(int a, int b)`
- `problem_001`: `max_int(int a, int b)`
- `problem_002`: `is_even(int n)`
- `problem_003`: `factorial(int n)`
- `problem_004`: `reverse_string(std::string s)`

`run_pipeline.py` は、指定された複数問題に対して次の順で処理します。

1. `make_design_prompt.py`
2. `run_design_generation.py`
3. `run_code_generation.py`
4. `run_similarity.py`
5. `run_tests.py`

例:

```bash
python scripts/run_pipeline.py --problem-ids problem_000 problem_001 problem_002 problem_003 problem_004 --model qwen2.5-coder:7b --temperature 0 --compiler C:\msys64\ucrt64\bin\g++.exe --ollama-url http://localhost:11434 --continue-on-error
```

`--continue-on-error` を指定すると、ある問題で失敗しても次の問題へ進みます。ただし、失敗した問題がある場合、スクリプト全体の終了コードは失敗として返します。

一括実行後に summary を更新します。

```bash
python scripts/summarize_results.py
```

summary には以下を出力します。

- `total_problems`
- `design_generated_count`
- `code_generated_count`
- `similarity_available_count`
- `average_similarity`
- `compile_success_count`
- `tests_passed_count`
- `pass_at_1`
- `failed_problem_ids`

## 今後の拡張

本格実験では HumanEval-X 本体を `data/raw/` に配置し、対象問題 ID を `data/selected/selected_ids.txt` で管理します。その後、`prepare_dataset.py` を拡張して HumanEval-X の C++ 問題を `experiments/humanevalx_cpp/problems/` 以下に展開する予定です。
