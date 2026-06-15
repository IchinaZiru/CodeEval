# HumanEval-X C++ JSONL のローカル準備

このリポジトリには、現時点で HumanEval-X C++ の生データ JSONL は含まれていない。

`data/raw/` はローカルデータ配置用のディレクトリであり、初期状態では `.gitkeep` だけを置いたプレースホルダである。HumanEval-X の生データは研究用ローカルデータとして扱い、原則として GitHub にはコミットしない。

## 配置先

HumanEval-X C++ の JSONL は、ローカル環境で次のパスに配置する。

```text
data/raw/humanevalx_cpp/humaneval_cpp.jsonl
```

この JSONL は、後続の `scripts/prepare_dataset.py` が HumanEval-X C++ 問題を `experiments/humanevalx_cpp/problems/` に展開するための入力になる予定である。現時点の `prepare_dataset.py` はまだ本格展開を行わず、ダミー問題レイアウトを確認するだけである。

## 依存関係

初期ダミーパイプライン用の `requirements.txt` は外部依存なしのまま維持する。HumanEval-X JSONL をエクスポートする場合だけ、別途 `requirements-dataset.txt` を使う。

```bash
pip install -r requirements-dataset.txt
```

## JSONL のエクスポート

Hugging Face datasets から HumanEval-X の C++ subset を読み込み、JSONL に保存する。

```bash
python scripts/export_humanevalx_cpp_jsonl.py
```

既定では、dataset name に `THUDM/humaneval-x`、subset に `cpp`、split に `test` を使う。Hugging Face 上では `zai-org/humaneval-x` として表示される場合があるため、スクリプトは既定 dataset の読み込みに失敗した場合に `zai-org/humaneval-x` も試す。

明示的に指定する場合:

```bash
python scripts/export_humanevalx_cpp_jsonl.py --dataset-name THUDM/humaneval-x --subset cpp --split test --output data/raw/humanevalx_cpp/humaneval_cpp.jsonl
```

## 必須フィールド

JSONL の各行には、少なくとも以下のフィールドが必要である。

- `task_id`
- `prompt`
- `declaration`
- `canonical_solution`
- `test`
- `example_test`

スクリプトは、これらのフィールドが欠けているレコードを検出した場合にエラー終了する。

## Git 管理方針

HumanEval-X の生データ JSONL は GitHub にコミットしない。`.gitignore` で以下を除外する。

```text
data/raw/humanevalx_cpp/*.jsonl
```

Codex は `generated_design/design.md` や `generated_code/generated.cpp` を作らない。これらは Ollama 上のローカル LLM が生成する出力として扱う。
