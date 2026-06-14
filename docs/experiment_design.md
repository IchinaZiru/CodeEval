# 実験設計

この実験では、HumanEval-X C++ の正解ソースコードを起点に、設計書を経由して C++ コードを再生成する。

## 目的

- 正解ソースコードから、ローカル LLM に設計書を逆生成させる。
- 生成された設計書から、ローカル LLM に C++ コードを再生成させる。
- 元の正解コードと再生成コードの類似度、テスト通過率を評価する。

## 現段階の範囲

現段階では HumanEval-X 本体は取り込まない。`problem_000`〜`problem_004` の小規模ダミー問題を使って、実験パイプラインの土台を確認する。

Codex は設計書や C++ コードを生成しない。Codex が整備するのは、ローカル LLM に渡すプロンプト、保存先、評価スクリプト、ドキュメントである。

## 評価項目

- 類似度: `difflib.SequenceMatcher` による単純な文字列類似度。
- テスト通過率: `test.cpp` と `generated.cpp` を一緒にコンパイルし、assert テストが通るかどうか。

## 今後の拡張

HumanEval-X 本体を `data/raw/` に配置したあと、対象問題を `data/selected/selected_ids.txt` で選び、`prepare_dataset.py` を拡張して C++ 問題を `experiments/humanevalx_cpp/problems/` に展開する。
