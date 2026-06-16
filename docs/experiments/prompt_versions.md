# Prompt Versions

This document records prompt-version differences for HumanEval-X C++ regeneration runs.

## prompt_v1_baseline

Initial baseline prompt.

- Generates a design document from `original.cpp`.
- Generates `generated.cpp` from `generated_design/design.md`.
- Requires the design to include a C++ function signature.
- Does not strongly enforce exact signature preservation or standalone include requirements.

## prompt_v2_signature_include

Current prompt version for the `feature/prompt-v2-signature-include` branch.

The prompt language remains Japanese-based to isolate the effect of signature/include constraints from any effect caused by translating the prompt into English.

### Design Prompt Changes

- The design document must include the exact C++ function signature in a fenced `cpp` block.
- The signature must preserve return type, function name, parameter order, parameter names, parameter types, value/reference qualifiers, and const qualifiers.
- Pass-by-value parameters must remain pass-by-value.
- The model must not rewrite signatures such as `std::string s` to `const std::string& s` or `vector<int> xs` to `const vector<int>& xs`.
- Namespace qualification in the signature must not be added or removed.

### Code Generation Prompt Changes

- `generated.cpp` must compile as its own translation unit together with `test.cpp`.
- The model must include every standard library header required by the generated function signature or implementation.
- The model must not rely on `test.cpp` for includes.
- If the exact signature uses unqualified standard library names such as `vector` or `string`, the generated file must add namespace support, for example `using namespace std;`, without changing the signature.
- The generated function signature must exactly match the signature in the design document.
- The generated output must not include Markdown, code fences, tests, or `main`.

### Metadata

Generation metadata now records:

- `prompt_version`
- `ollama_timeout`
- `model`
- `temperature`
- `ollama_url`
- `prompt_path`
- `output_path`
- `timestamp`

Model-run metadata now records:

- `prompt_version`
- `ollama_timeout`
- the planned `prepare_dataset.py` and `run_pipeline.py` commands

## Recommended Command Shape

Use an explicit prompt version when starting a model run:

```bash
python scripts/run_model_experiment.py --prompt-version prompt_v2_signature_include --model qwen3-coder:latest --limit 10 --compiler g++ --continue-on-error --dry-run
```

Remove `--dry-run` only when ready to run the actual local Ollama experiment.
