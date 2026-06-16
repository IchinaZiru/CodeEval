"""Shared helpers for HumanEval-X C++ evaluation summaries."""

from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]

CODE_METRIC_FIELDS = [
    "text_similarity",
    "normalized_edit_similarity",
    "token_jaccard_similarity",
    "token_cosine_similarity",
    "line_count_original",
    "line_count_generated",
    "line_count_ratio",
    "token_count_original",
    "token_count_generated",
    "token_count_ratio",
    "brace_depth_max_original",
    "brace_depth_max_generated",
    "brace_depth_diff",
    "function_signature_original",
    "function_signature_generated",
    "function_signature_similarity",
    "signature_exact_match",
    "original_include_count",
    "generated_include_count",
    "generated_has_include_vector",
    "generated_has_include_string",
    "generated_has_include_map",
    "generated_has_include_set",
    "generated_has_include_algorithm",
    "generated_has_include_cmath",
    "generated_has_using_namespace_std",
    "generated_uses_vector",
    "generated_uses_string",
    "generated_uses_map",
    "generated_uses_set",
    "generated_uses_sort",
    "generated_uses_abs_or_math",
    "include_likely_complete",
]

DESIGN_METRIC_FIELDS = [
    "design_exists",
    "design_chars",
    "design_lines",
    "has_cpp_signature_block",
    "has_input_description",
    "has_output_description",
    "has_algorithm_description",
    "has_edge_case_description",
    "has_constraints_description",
    "mentions_return_value",
    "mentions_parameter",
    "design_quality_score",
]

TEST_SUMMARY_FIELDS = [
    "problem_id",
    "status",
    "passed",
    "compile_returncode",
    "run_returncode",
    "reason",
    "generated_path",
    "test_path",
    "generated_exists",
    "design_exists",
]

COMBINED_SUMMARY_FIELDS = [
    "problem_id",
    "task_id",
    "status",
    "passed",
    "compile_returncode",
    "run_returncode",
    "reason",
    "text_similarity",
    "normalized_edit_similarity",
    "token_jaccard_similarity",
    "token_cosine_similarity",
    "dolos_similarity",
    "dolos_notes",
    "line_count_original",
    "line_count_generated",
    "line_count_ratio",
    "token_count_original",
    "token_count_generated",
    "token_count_ratio",
    "brace_depth_max_original",
    "brace_depth_max_generated",
    "brace_depth_diff",
    "function_signature_similarity",
    "signature_exact_match",
    "original_include_count",
    "generated_include_count",
    "generated_has_include_vector",
    "generated_has_include_string",
    "generated_has_include_map",
    "generated_has_include_set",
    "generated_has_include_algorithm",
    "generated_has_include_cmath",
    "generated_has_using_namespace_std",
    "generated_uses_vector",
    "generated_uses_string",
    "generated_uses_map",
    "generated_uses_set",
    "generated_uses_sort",
    "generated_uses_abs_or_math",
    "include_likely_complete",
    "design_exists",
    "design_chars",
    "design_lines",
    "has_cpp_signature_block",
    "has_input_description",
    "has_output_description",
    "has_algorithm_description",
    "has_edge_case_description",
    "has_constraints_description",
    "mentions_return_value",
    "mentions_parameter",
    "design_quality_score",
    "generated_exists",
    "generated_path",
    "test_path",
]


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT_DIR / path


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT_DIR).as_posix()
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def problem_dirs(run_dir: Path) -> list[Path]:
    problems_dir = run_dir / "problems"
    if not problems_dir.exists():
        return []
    return sorted(path for path in problems_dir.glob("problem_*") if path.is_dir())


def safe_ratio(numerator: int | float, denominator: int | float) -> float | None:
    if denominator == 0:
        return None
    return float(numerator) / float(denominator)


def numeric_values(rows: list[dict[str, Any]], field: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = row.get(field)
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            values.append(float(value))
            continue
        if isinstance(value, str) and value.strip():
            try:
                values.append(float(value))
            except ValueError:
                pass
    return values


def average(rows: list[dict[str, Any]], field: str) -> float | None:
    values = numeric_values(rows, field)
    if not values:
        return None
    return sum(values) / len(values)


def strip_comments_and_simplify_literals(code: str) -> str:
    code = re.sub(r"/\*.*?\*/", " ", code, flags=re.DOTALL)
    code = re.sub(r"//.*", " ", code)
    code = re.sub(r'R"[^()\\]*(?:\([^"]*\))?[^"]*"', " STRING_LITERAL ", code)
    code = re.sub(r'"(?:\\.|[^"\\])*"', " STRING_LITERAL ", code)
    code = re.sub(r"'(?:\\.|[^'\\])*'", " CHAR_LITERAL ", code)
    return code


TOKEN_RE = re.compile(
    r"[A-Za-z_]\w*|\d+(?:\.\d+)?|==|!=|<=|>=|&&|\|\||::|->|\+\+|--|[{}()[\];,.*+\-/%<>=!&|^?:]"
)


def tokenize_cpp(code: str) -> list[str]:
    return TOKEN_RE.findall(strip_comments_and_simplify_literals(code))


def token_jaccard(original_tokens: list[str], generated_tokens: list[str]) -> float | None:
    original_set = set(original_tokens)
    generated_set = set(generated_tokens)
    union = original_set | generated_set
    if not union:
        return None
    return len(original_set & generated_set) / len(union)


def token_cosine(original_tokens: list[str], generated_tokens: list[str]) -> float | None:
    original_counts = Counter(original_tokens)
    generated_counts = Counter(generated_tokens)
    keys = set(original_counts) | set(generated_counts)
    if not keys:
        return None
    dot = sum(original_counts[key] * generated_counts[key] for key in keys)
    original_norm = math.sqrt(sum(value * value for value in original_counts.values()))
    generated_norm = math.sqrt(sum(value * value for value in generated_counts.values()))
    if original_norm == 0 or generated_norm == 0:
        return None
    return dot / (original_norm * generated_norm)


def max_brace_depth(code: str) -> int:
    depth = 0
    maximum = 0
    for char in strip_comments_and_simplify_literals(code):
        if char == "{":
            depth += 1
            maximum = max(maximum, depth)
        elif char == "}":
            depth = max(0, depth - 1)
    return maximum


def include_names(code: str) -> list[str]:
    return re.findall(r"^\s*#\s*include\s*[<\"]([^>\"]+)[>\"]", code, flags=re.MULTILINE)


def has_include(includes: list[str], name: str) -> bool:
    return name in includes or "bits/stdc++.h" in includes


def function_signature(code: str) -> str:
    cleaned = re.sub(r"^\s*#.*$", "", code, flags=re.MULTILINE)
    cleaned = re.sub(r"\busing\s+namespace\s+\w+\s*;", "", cleaned)
    pattern = re.compile(
        r"([A-Za-z_][\w:<>,~\s*&]*?)\s+([A-Za-z_]\w*)\s*\(([^;{}()]*(?:\([^)]*\)[^;{}()]*)*)\)\s*(?:const\s*)?\{",
        flags=re.DOTALL,
    )
    for match in pattern.finditer(cleaned):
        candidate = match.group(0).rsplit("{", 1)[0].strip()
        if re.match(r"^(if|for|while|switch|catch)\b", candidate.strip()):
            continue
        return candidate
    return ""


def normalize_signature(signature: str) -> str:
    signature = re.sub(r"\s+", " ", signature.strip())
    signature = re.sub(r"\s*([(),<>*&])\s*", r"\1", signature)
    signature = re.sub(r"\s*::\s*", "::", signature)
    signature = re.sub(r"\s+", " ", signature).strip()
    return signature


def code_usage_flags(code: str) -> dict[str, bool]:
    stripped = strip_comments_and_simplify_literals(code)
    return {
        "generated_uses_vector": bool(re.search(r"\b(?:std::)?vector\s*<", stripped)),
        "generated_uses_string": bool(re.search(r"\b(?:std::)?string\b", stripped)),
        "generated_uses_map": bool(re.search(r"\b(?:std::)?map\s*<", stripped)),
        "generated_uses_set": bool(re.search(r"\b(?:std::)?set\s*<", stripped)),
        "generated_uses_sort": bool(re.search(r"\b(?:std::)?sort\s*\(", stripped)),
        "generated_uses_abs_or_math": bool(
            re.search(r"\b(?:std::)?(?:abs|sqrt|pow|floor|ceil|sin|cos|tan|log|exp)\s*\(", stripped)
        ),
    }


def include_likely_complete(includes: list[str], usage: dict[str, bool]) -> bool:
    checks = [
        (usage["generated_uses_vector"], has_include(includes, "vector")),
        (usage["generated_uses_string"], has_include(includes, "string")),
        (usage["generated_uses_map"], has_include(includes, "map")),
        (usage["generated_uses_set"], has_include(includes, "set")),
        (usage["generated_uses_sort"], has_include(includes, "algorithm")),
        (usage["generated_uses_abs_or_math"], has_include(includes, "cmath") or has_include(includes, "math.h")),
    ]
    return all(present for used, present in checks if used)


def compute_code_metrics_for_problem(problem_dir: Path) -> dict[str, Any]:
    problem_id = problem_dir.name
    original_path = problem_dir / "original.cpp"
    generated_path = problem_dir / "generated_code" / "generated.cpp"

    payload: dict[str, Any] = {
        "problem_id": problem_id,
        "original_path": display_path(original_path),
        "generated_path": display_path(generated_path),
        "original_exists": original_path.exists(),
        "generated_exists": generated_path.exists(),
    }

    if not original_path.exists() or not generated_path.exists():
        payload.update({field: None for field in CODE_METRIC_FIELDS})
        payload["status"] = "missing_original_or_generated"
        return payload

    original_text = original_path.read_text(encoding="utf-8")
    generated_text = generated_path.read_text(encoding="utf-8")
    original_tokens = tokenize_cpp(original_text)
    generated_tokens = tokenize_cpp(generated_text)
    original_includes = include_names(original_text)
    generated_includes = include_names(generated_text)
    usage = code_usage_flags(generated_text)
    original_signature = normalize_signature(function_signature(original_text))
    generated_signature = normalize_signature(function_signature(generated_text))

    payload.update(
        {
            "status": "success",
            "text_similarity": SequenceMatcher(None, original_text, generated_text).ratio(),
            "normalized_edit_similarity": SequenceMatcher(None, original_text, generated_text).ratio(),
            "token_jaccard_similarity": token_jaccard(original_tokens, generated_tokens),
            "token_cosine_similarity": token_cosine(original_tokens, generated_tokens),
            "line_count_original": len(original_text.splitlines()),
            "line_count_generated": len(generated_text.splitlines()),
            "line_count_ratio": safe_ratio(len(generated_text.splitlines()), len(original_text.splitlines())),
            "token_count_original": len(original_tokens),
            "token_count_generated": len(generated_tokens),
            "token_count_ratio": safe_ratio(len(generated_tokens), len(original_tokens)),
            "brace_depth_max_original": max_brace_depth(original_text),
            "brace_depth_max_generated": max_brace_depth(generated_text),
            "brace_depth_diff": max_brace_depth(generated_text) - max_brace_depth(original_text),
            "function_signature_original": original_signature,
            "function_signature_generated": generated_signature,
            "function_signature_similarity": SequenceMatcher(None, original_signature, generated_signature).ratio()
            if original_signature or generated_signature
            else None,
            "signature_exact_match": bool(original_signature and original_signature == generated_signature),
            "original_include_count": len(original_includes),
            "generated_include_count": len(generated_includes),
            "generated_has_include_vector": has_include(generated_includes, "vector"),
            "generated_has_include_string": has_include(generated_includes, "string"),
            "generated_has_include_map": has_include(generated_includes, "map"),
            "generated_has_include_set": has_include(generated_includes, "set"),
            "generated_has_include_algorithm": has_include(generated_includes, "algorithm"),
            "generated_has_include_cmath": has_include(generated_includes, "cmath") or has_include(generated_includes, "math.h"),
            "generated_has_using_namespace_std": bool(re.search(r"\busing\s+namespace\s+std\s*;", generated_text)),
            **usage,
            "include_likely_complete": include_likely_complete(generated_includes, usage),
        }
    )
    return payload


def contains_any(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def compute_design_metrics_for_problem(problem_dir: Path) -> dict[str, Any]:
    problem_id = problem_dir.name
    design_path = problem_dir / "generated_design" / "design.md"
    payload: dict[str, Any] = {
        "problem_id": problem_id,
        "design_path": display_path(design_path),
        "design_exists": design_path.exists(),
    }

    if not design_path.exists():
        payload.update({field: False for field in DESIGN_METRIC_FIELDS if field.startswith("has_") or field.startswith("mentions_")})
        payload.update({"design_chars": 0, "design_lines": 0, "design_quality_score": 0.0, "status": "missing_design"})
        return payload

    text = design_path.read_text(encoding="utf-8")
    checks = {
        "has_cpp_signature_block": bool(re.search(r"```(?:cpp|c\+\+|cc|cxx)\s*\n.*?\)", text, flags=re.IGNORECASE | re.DOTALL)),
        "has_input_description": contains_any(text, ["入力", "引数", "parameter", "input"]),
        "has_output_description": contains_any(text, ["出力", "返り値", "戻り値", "return", "output"]),
        "has_algorithm_description": contains_any(text, ["手順", "アルゴリズム", "処理", "algorithm", "step"]),
        "has_edge_case_description": contains_any(text, ["境界", "edge", "corner", "empty", "空"]),
        "has_constraints_description": contains_any(text, ["制約", "constraint", "must", "should"]),
        "mentions_return_value": contains_any(text, ["返り値", "戻り値", "return value", "return"]),
        "mentions_parameter": contains_any(text, ["引数", "parameter", "argument"]),
    }
    payload.update(
        {
            "status": "success",
            "design_chars": len(text),
            "design_lines": len(text.splitlines()),
            **checks,
            "design_quality_score": sum(1 for value in checks.values() if value) / len(checks),
        }
    )
    return payload


def test_summary_row(problem_dir: Path) -> dict[str, Any]:
    problem_id = problem_dir.name
    test_path = problem_dir / "test.cpp"
    generated_path = problem_dir / "generated_code" / "generated.cpp"
    design_path = problem_dir / "generated_design" / "design.md"
    test_results = read_json(problem_dir / "results" / "test_results.json") or {}

    status = str(test_results.get("status") or "missing_test_result")
    reason = test_results.get("reason", "")
    if not generated_path.exists() and status == "missing_test_result":
        status = "missing_generated_code"
        reason = "generated_code/generated.cpp was not found."

    return {
        "problem_id": problem_id,
        "status": status,
        "passed": test_results.get("passed", False),
        "compile_returncode": test_results.get("compile_returncode", ""),
        "run_returncode": test_results.get("run_returncode", ""),
        "reason": reason,
        "generated_path": display_path(generated_path),
        "test_path": display_path(test_path),
        "generated_exists": generated_path.exists(),
        "design_exists": design_path.exists(),
    }


def metadata_task_id(problem_dir: Path) -> str:
    metadata = read_json(problem_dir / "metadata.json") or {}
    return str(metadata.get("task_id", ""))


def combined_row(problem_dir: Path) -> dict[str, Any]:
    tests = test_summary_row(problem_dir)
    code_metrics = compute_code_metrics_for_problem(problem_dir)
    design_metrics = compute_design_metrics_for_problem(problem_dir)
    similarity = read_json(problem_dir / "results" / "similarity.json") or {}

    row: dict[str, Any] = {
        **tests,
        "task_id": metadata_task_id(problem_dir),
        "dolos_similarity": "",
        "dolos_notes": "",
    }
    for field in CODE_METRIC_FIELDS:
        row[field] = code_metrics.get(field, "")
    for field in DESIGN_METRIC_FIELDS:
        row[field] = design_metrics.get(field, "")

    if similarity.get("similarity") is not None:
        row["text_similarity"] = similarity.get("similarity")
    return row


def collect_run_rows(run_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    tests: list[dict[str, Any]] = []
    combined: list[dict[str, Any]] = []
    for problem_dir in problem_dirs(run_dir):
        tests.append(test_summary_row(problem_dir))
        combined.append(combined_row(problem_dir))
    return tests, combined


def status_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return counts


def rows_where(rows: list[dict[str, Any]], passed: bool) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("passed") is passed]


def run_summary_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    passed_count = sum(1 for row in rows if row.get("passed") is True)
    failed_count = total - passed_count
    passed_rows = rows_where(rows, True)
    failed_rows = [row for row in rows if row.get("passed") is not True]
    return {
        "total": total,
        "passed": passed_count,
        "failed": failed_count,
        "pass_rate": safe_ratio(passed_count, total),
        "status_counts": status_counts(rows),
        "average_text_similarity": average(rows, "text_similarity"),
        "average_text_similarity_passed": average(passed_rows, "text_similarity"),
        "average_text_similarity_failed": average(failed_rows, "text_similarity"),
        "average_token_jaccard_similarity": average(rows, "token_jaccard_similarity"),
        "average_token_cosine_similarity": average(rows, "token_cosine_similarity"),
        "average_dolos_similarity": average(rows, "dolos_similarity"),
        "average_design_quality_score": average(rows, "design_quality_score"),
        "average_design_quality_score_passed": average(passed_rows, "design_quality_score"),
        "average_design_quality_score_failed": average(failed_rows, "design_quality_score"),
    }


def generation_failed_or_timeout_count(rows: list[dict[str, Any]]) -> int:
    target_statuses = {
        "generation_failed",
        "missing_generated_code",
        "missing_test_result",
        "compile_timeout",
        "run_timeout",
        "timeout",
    }
    return sum(1 for row in rows if str(row.get("status") or "") in target_statuses)
