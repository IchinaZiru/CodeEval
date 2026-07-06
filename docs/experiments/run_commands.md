# 実験実行コマンド集

この文書は、CodeEval の v3 / pass@k 実験で使う実行コマンドをまとめる。

Codex は `generated_design/design.md`、`generated_code/generated.cpp`、実験結果 JSON / CSV を手動編集しない。これらは Ollama 上のローカル LLM と実験スクリプトが生成する。

## 前提

PowerShell でリポジトリ直下から実行する。

```powershell
cd C:\Users\kikumanetworklab\Documents\GitHub\CodeEval
```

Ollama はローカルで起動している前提とする。

```powershell
ollama list
```

C++ コンパイラは MSYS2 の `g++` を使う例に統一する。

```powershell
C:\msys64\ucrt64\bin\g++.exe --version
```

## v3 pass@k 実験の標準設定

`prompt_v3_general_design` では、設計文書生成プロンプトを一般化する。codegen self-check は追加しない。

標準設定:

```text
prompt_version: prompt_v3_general_design
problem count: 10
design temperature: 0.0
pass@1 temperature: 0.0
pass@3 temperature: 0.2
pass@3 samples: 3
compiler: C:\msys64\ucrt64\bin\g++.exe
std: c++17
ollama_url: http://localhost:11434
ollama_timeout: 120.0
test_timeout: 10.0
```

保存先:

```text
experiments/humanevalx_cpp_runs/prompt_v3_general_design/<model_dir_name>/
```

例:

```text
gpt-oss:20b          -> gpt-oss_20b
qwen3-coder:latest  -> qwen3-coder_latest
phi4:latest         -> phi4_latest
```

## dry-run

実験前に、保存先と実行予定コマンドだけを確認する。

```powershell
python scripts/run_passk_experiment.py `
  --model qwen3-coder:latest `
  --prompt-version prompt_v3_general_design `
  --limit 10 `
  --start-index 0 `
  --design-temperature 0.0 `
  --pass1-temperature 0.0 `
  --pass3-temperature 0.2 `
  --pass3-samples 3 `
  --compiler C:\msys64\ucrt64\bin\g++.exe `
  --std c++17 `
  --ollama-url http://localhost:11434 `
  --ollama-timeout 120.0 `
  --test-timeout 10.0 `
  --continue-on-error `
  --dry-run
```

`--dry-run` では、ディレクトリ作成、Ollama 呼び出し、生成物作成、評価実行は行わない。

## 既存 run を上書きしない実行

既存の run directory がないモデルで実行する場合は、`--force-run` を付けない。

```powershell
python scripts/run_passk_experiment.py `
  --model phi4:latest `
  --prompt-version prompt_v3_general_design `
  --limit 10 `
  --start-index 0 `
  --design-temperature 0.0 `
  --pass1-temperature 0.0 `
  --pass3-temperature 0.2 `
  --pass3-samples 3 `
  --compiler C:\msys64\ucrt64\bin\g++.exe `
  --std c++17 `
  --ollama-url http://localhost:11434 `
  --ollama-timeout 120.0 `
  --test-timeout 10.0 `
  --continue-on-error
```

既存の run directory がある場合、`--force-run` なしでは停止する。

## 既存 run を上書きして再実行

以前の v3 プロンプトで生成した結果を、新しい v3 実装で作り直す場合は `--force-run` を付ける。

注意: `--force-run` を付けると、同じ run directory 内の生成設計書、生成 C++、結果 JSON、summary が更新される。

上書き対象の例:

```text
generated_design/design.md
generated_code/generated.cpp
generated_code/pass1/sample_001/generated.cpp
generated_code/pass3/sample_*/generated.cpp
results/*.json
results/pass1/sample_001/*.json
results/pass3/sample_*/*.json
summary/passk_summary.csv
summary/passk_metrics.json
run_metadata.json
```

### gpt-oss:20b

```powershell
python scripts/run_passk_experiment.py `
  --model gpt-oss:20b `
  --prompt-version prompt_v3_general_design `
  --limit 10 `
  --start-index 0 `
  --design-temperature 0.0 `
  --pass1-temperature 0.0 `
  --pass3-temperature 0.2 `
  --pass3-samples 3 `
  --compiler C:\msys64\ucrt64\bin\g++.exe `
  --std c++17 `
  --ollama-url http://localhost:11434 `
  --ollama-timeout 120.0 `
  --test-timeout 10.0 `
  --continue-on-error `
  --force-run
```

### qwen3-coder:latest

```powershell
python scripts/run_passk_experiment.py `
  --model qwen3-coder:latest `
  --prompt-version prompt_v3_general_design `
  --limit 10 `
  --start-index 0 `
  --design-temperature 0.0 `
  --pass1-temperature 0.0 `
  --pass3-temperature 0.2 `
  --pass3-samples 3 `
  --compiler C:\msys64\ucrt64\bin\g++.exe `
  --std c++17 `
  --ollama-url http://localhost:11434 `
  --ollama-timeout 120.0 `
  --test-timeout 10.0 `
  --continue-on-error `
  --force-run
```

### qwen2.5-coder:32b

```powershell
python scripts/run_passk_experiment.py `
  --model qwen2.5-coder:32b `
  --prompt-version prompt_v3_general_design `
  --limit 10 `
  --start-index 0 `
  --design-temperature 0.0 `
  --pass1-temperature 0.0 `
  --pass3-temperature 0.2 `
  --pass3-samples 3 `
  --compiler C:\msys64\ucrt64\bin\g++.exe `
  --std c++17 `
  --ollama-url http://localhost:11434 `
  --ollama-timeout 120.0 `
  --test-timeout 10.0 `
  --continue-on-error `
  --force-run
```

### phi4:latest

```powershell
python scripts/run_passk_experiment.py `
  --model phi4:latest `
  --prompt-version prompt_v3_general_design `
  --limit 10 `
  --start-index 0 `
  --design-temperature 0.0 `
  --pass1-temperature 0.0 `
  --pass3-temperature 0.2 `
  --pass3-samples 3 `
  --compiler C:\msys64\ucrt64\bin\g++.exe `
  --std c++17 `
  --ollama-url http://localhost:11434 `
  --ollama-timeout 120.0 `
  --test-timeout 10.0 `
  --continue-on-error `
  --force-run
```

## 少数問題での動作確認

長い実験の前に、1問だけ確認する場合。

```powershell
python scripts/run_passk_experiment.py `
  --model phi4:latest `
  --prompt-version prompt_v3_general_design `
  --limit 1 `
  --start-index 0 `
  --design-temperature 0.0 `
  --pass1-temperature 0.0 `
  --pass3-temperature 0.2 `
  --pass3-samples 3 `
  --compiler C:\msys64\ucrt64\bin\g++.exe `
  --std c++17 `
  --ollama-url http://localhost:11434 `
  --ollama-timeout 120.0 `
  --test-timeout 10.0 `
  --continue-on-error
```

## pass@k 集計

実験後、run directory ごとに集計する。

### gpt-oss:20b

```powershell
python scripts/summarize_passk_results.py `
  --run-dir experiments\humanevalx_cpp_runs\prompt_v3_general_design\gpt-oss_20b
```

### qwen3-coder:latest

```powershell
python scripts/summarize_passk_results.py `
  --run-dir experiments\humanevalx_cpp_runs\prompt_v3_general_design\qwen3-coder_latest
```

### qwen2.5-coder:32b

```powershell
python scripts/summarize_passk_results.py `
  --run-dir experiments\humanevalx_cpp_runs\prompt_v3_general_design\qwen2.5-coder_32b
```

### phi4:latest

```powershell
python scripts/summarize_passk_results.py `
  --run-dir experiments\humanevalx_cpp_runs\prompt_v3_general_design\phi4_latest
```

出力:

```text
<run-dir>/summary/passk_summary.csv
<run-dir>/summary/passk_metrics.json
```

`passk_metrics.json` には、少なくとも以下が入る。

```text
total_problems
pass@1_temp0.0_count
pass@1_temp0.0_rate
pass@3_temp0.2_count
pass@3_temp0.2_rate
pass3_total_samples_per_problem
```

`passk_summary.csv` では、問題ごとに pass@1、pass@3、sample 単位の status、失敗理由を確認できる。

## v3.1 pass@k 実験: prompt_v3_general_design_v2

`prompt_v3_general_design_v2` は、v3 general design の補強版である。
既存の `prompt_v3_general_design` は上書きせず、v3.1 相当の別 prompt version として扱う。

v3.1 では design prompt のみを改善する。codegen prompt は v3 と同じまま維持し、codegen self-check は追加しない。
self-check は v4 の対象として残す。

目的は、汎用性を維持しながら、処理対象、無視条件、状態更新、結果追加タイミング、ループ後処理などの具体性を設計書に補うことである。

標準設定:

```text
prompt_version: prompt_v3_general_design_v2
problem count: 10
design temperature: 0.0
pass@1 temperature: 0.0
pass@3 temperature: 0.2
pass@3 samples: 3
compiler: C:\msys64\ucrt64\bin\g++.exe
std: c++17
ollama_url: http://localhost:11434
ollama_timeout: 120.0
test_timeout: 10.0
```

保存先:

```text
experiments/humanevalx_cpp_runs/prompt_v3_general_design_v2/<model_dir_name>/
```

### v3.1 design prompt dry-run

```powershell
python scripts/make_design_prompt.py `
  --problem-id problem_001 `
  --prompt-version prompt_v3_general_design_v2 `
  --dry-run
```

### v3.1 pass@k dry-run

```powershell
python scripts/run_passk_experiment.py `
  --model qwen3-coder:latest `
  --prompt-version prompt_v3_general_design_v2 `
  --limit 10 `
  --start-index 0 `
  --design-temperature 0.0 `
  --pass1-temperature 0.0 `
  --pass3-temperature 0.2 `
  --pass3-samples 3 `
  --compiler C:\msys64\ucrt64\bin\g++.exe `
  --std c++17 `
  --ollama-url http://localhost:11434 `
  --ollama-timeout 120.0 `
  --test-timeout 10.0 `
  --continue-on-error `
  --dry-run
```

### v3.1 本実験: gpt-oss:20b

```powershell
python scripts/run_passk_experiment.py `
  --model gpt-oss:20b `
  --prompt-version prompt_v3_general_design_v2 `
  --limit 10 `
  --start-index 0 `
  --design-temperature 0.0 `
  --pass1-temperature 0.0 `
  --pass3-temperature 0.2 `
  --pass3-samples 3 `
  --compiler C:\msys64\ucrt64\bin\g++.exe `
  --std c++17 `
  --ollama-url http://localhost:11434 `
  --ollama-timeout 120.0 `
  --test-timeout 10.0 `
  --continue-on-error
```

### v3.1 本実験: phi4:latest

```powershell
python scripts/run_passk_experiment.py `
  --model phi4:latest `
  --prompt-version prompt_v3_general_design_v2 `
  --limit 10 `
  --start-index 0 `
  --design-temperature 0.0 `
  --pass1-temperature 0.0 `
  --pass3-temperature 0.2 `
  --pass3-samples 3 `
  --compiler C:\msys64\ucrt64\bin\g++.exe `
  --std c++17 `
  --ollama-url http://localhost:11434 `
  --ollama-timeout 120.0 `
  --test-timeout 10.0 `
  --continue-on-error
```

### v3.1 本実験: qwen3-coder:latest

```powershell
python scripts/run_passk_experiment.py `
  --model qwen3-coder:latest `
  --prompt-version prompt_v3_general_design_v2 `
  --limit 10 `
  --start-index 0 `
  --design-temperature 0.0 `
  --pass1-temperature 0.0 `
  --pass3-temperature 0.2 `
  --pass3-samples 3 `
  --compiler C:\msys64\ucrt64\bin\g++.exe `
  --std c++17 `
  --ollama-url http://localhost:11434 `
  --ollama-timeout 120.0 `
  --test-timeout 10.0 `
  --continue-on-error
```

既存の v3.1 run directory を上書きして再実行する場合だけ、上記の本実験コマンドに `--force-run` を追加する。

### v3.1 pass@k 集計

```powershell
python scripts/summarize_passk_results.py `
  --run-dir experiments\humanevalx_cpp_runs\prompt_v3_general_design_v2\gpt-oss_20b
```

```powershell
python scripts/summarize_passk_results.py `
  --run-dir experiments\humanevalx_cpp_runs\prompt_v3_general_design_v2\phi4_latest
```

```powershell
python scripts/summarize_passk_results.py `
  --run-dir experiments\humanevalx_cpp_runs\prompt_v3_general_design_v2\qwen3-coder_latest
```

## v4 pass@k 実験: prompt_v4_general_design_self_check

`prompt_v4_general_design_self_check` では、design prompt は `prompt_v3_general_design` と同じにする。
変更するのは codegen prompt だけで、最終出力前の self-check を追加する。

self-check はモデル内部の確認として使わせる。self-check の結果、チェックリスト、説明文は出力させない。
最終出力は `generated.cpp` に保存できる C++ コードのみである。

標準設定:

```text
prompt_version: prompt_v4_general_design_self_check
problem count: 10
design temperature: 0.0
pass@1 temperature: 0.0
pass@3 temperature: 0.2
pass@3 samples: 3
compiler: C:\msys64\ucrt64\bin\g++.exe
std: c++17
ollama_url: http://localhost:11434
ollama_timeout: 120.0
test_timeout: 10.0
```

保存先:

```text
experiments/humanevalx_cpp_runs/prompt_v4_general_design_self_check/<model_dir_name>/
```

### v4 design prompt dry-run

v4 の design prompt は v3 と同じ内容になる。

```powershell
python scripts/make_design_prompt.py `
  --problem-id problem_001 `
  --prompt-version prompt_v4_general_design_self_check `
  --dry-run
```

### v4 pass@k dry-run

```powershell
python scripts/run_passk_experiment.py `
  --model qwen3-coder:latest `
  --prompt-version prompt_v4_general_design_self_check `
  --limit 10 `
  --start-index 0 `
  --design-temperature 0.0 `
  --pass1-temperature 0.0 `
  --pass3-temperature 0.2 `
  --pass3-samples 3 `
  --compiler C:\msys64\ucrt64\bin\g++.exe `
  --std c++17 `
  --ollama-url http://localhost:11434 `
  --ollama-timeout 120.0 `
  --test-timeout 10.0 `
  --continue-on-error `
  --dry-run
```

### v4 本実験: gpt-oss:20b

```powershell
python scripts/run_passk_experiment.py `
  --model gpt-oss:20b `
  --prompt-version prompt_v4_general_design_self_check `
  --limit 10 `
  --start-index 0 `
  --design-temperature 0.0 `
  --pass1-temperature 0.0 `
  --pass3-temperature 0.2 `
  --pass3-samples 3 `
  --compiler C:\msys64\ucrt64\bin\g++.exe `
  --std c++17 `
  --ollama-url http://localhost:11434 `
  --ollama-timeout 120.0 `
  --test-timeout 10.0 `
  --continue-on-error
```

### v4 本実験: phi4:latest

```powershell
python scripts/run_passk_experiment.py `
  --model phi4:latest `
  --prompt-version prompt_v4_general_design_self_check `
  --limit 10 `
  --start-index 0 `
  --design-temperature 0.0 `
  --pass1-temperature 0.0 `
  --pass3-temperature 0.2 `
  --pass3-samples 3 `
  --compiler C:\msys64\ucrt64\bin\g++.exe `
  --std c++17 `
  --ollama-url http://localhost:11434 `
  --ollama-timeout 120.0 `
  --test-timeout 10.0 `
  --continue-on-error
```

### v4 本実験: qwen3-coder:latest

```powershell
python scripts/run_passk_experiment.py `
  --model qwen3-coder:latest `
  --prompt-version prompt_v4_general_design_self_check `
  --limit 10 `
  --start-index 0 `
  --design-temperature 0.0 `
  --pass1-temperature 0.0 `
  --pass3-temperature 0.2 `
  --pass3-samples 3 `
  --compiler C:\msys64\ucrt64\bin\g++.exe `
  --std c++17 `
  --ollama-url http://localhost:11434 `
  --ollama-timeout 120.0 `
  --test-timeout 10.0 `
  --continue-on-error
```

既存の v4 run directory を上書きして再実行する場合だけ、上記の本実験コマンドに `--force-run` を追加する。

### v4 pass@k 集計

```powershell
python scripts/summarize_passk_results.py `
  --run-dir experiments\humanevalx_cpp_runs\prompt_v4_general_design_self_check\gpt-oss_20b
```

```powershell
python scripts/summarize_passk_results.py `
  --run-dir experiments\humanevalx_cpp_runs\prompt_v4_general_design_self_check\phi4_latest
```

```powershell
python scripts/summarize_passk_results.py `
  --run-dir experiments\humanevalx_cpp_runs\prompt_v4_general_design_self_check\qwen3-coder_latest
```

## run_passk_experiment.py の主要引数

```text
--model
  Ollama model name. Required.

--prompt-version
  保存先ディレクトリ名と metadata 用の prompt version。
  v3 では prompt_v3_general_design を使う。

--runs-root
  run 保存先の root。
  default: experiments/humanevalx_cpp_runs

--problem-ids
  明示的に対象 problem_id を指定する。
  例: --problem-ids problem_000 problem_001

--limit
  problem_000 から何問使うか。
  default: 10

--start-index
  HumanEval-X JSONL から選ぶ開始 index。
  default: 0

--design-temperature
  design.md 生成時の temperature。
  default: 0.0

--pass1-temperature
  pass@1 sample の code generation temperature。
  default: 0.0

--pass3-temperature
  pass@3 samples の code generation temperature。
  default: 0.2

--pass3-samples
  pass@3 の sample 数。
  default: 3

--compiler
  C++ compiler。
  推奨: C:\msys64\ucrt64\bin\g++.exe

--std
  C++ standard。
  default: c++17

--ollama-url
  Ollama API URL。
  default: http://localhost:11434

--ollama-timeout
  Ollama API request timeout seconds。
  default: 120.0

--test-timeout
  compile / test execution timeout seconds。
  default: 10.0

--continue-on-error
  失敗した problem や sample があっても次へ進む。

--force-run
  既存 run directory の再利用・上書きを許可する。

--dry-run
  実行予定コマンドだけ表示し、生成や評価は実行しない。

--skip-prepare
  prepare_dataset.py を実行せず、既存の problem directory を使う。

--skip-design-generation
  design.md を再生成せず、既存の generated_design/design.md を使う。

--validate-original
  prepare_dataset.py 実行時に original.cpp + test.cpp の検証を行う。
```

## summarize_passk_results.py の引数

```text
--run-dir
  集計対象の run directory。必須。

--output-dir
  summary の出力先。
  省略時は <run-dir>/summary。
```

## 結果の読み方

`pass@1_temp0.0_rate` は、1回生成でテストに通った問題の割合である。

`pass@3_temp0.2_rate` は、3回生成のうち1回でもテストに通った問題の割合である。

pass@3 は問題単位の成功率なので、sample 単位の成功率とは異なる。

例:

```text
sample_001: passed
sample_002: compile_failed
sample_003: passed
```

この場合、問題単位では pass@3 は成功だが、sample 単位では 2/3 成功である。

失敗理由を見るときは、次を区別する。

```text
compile_failed
  C++ としてコンパイルできない。include 不足、namespace 不足、シグネチャ不一致など。

test_failed / run_failed
  コンパイルはできたが、assert に失敗した。アルゴリズムや edge case の誤り。

generation_failed
  Ollama API 呼び出しや生成処理の失敗。
```

## 注意

既存 run を残したい場合は `--force-run` を付けない。

別条件として保存したい場合は、`--prompt-version` を変える。ただし、`make_design_prompt.py` 側で対応する prompt version を実装しておく必要がある。

実験結果は `experiments/humanevalx_cpp_runs/` 配下に保存される。このディレクトリはローカル実験結果であり、原則 Git に commit しない。
