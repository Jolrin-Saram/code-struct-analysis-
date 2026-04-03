from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from core.config.schema import AnalysisConfig


RISK_RULES: list[dict[str, Any]] = [
    {
        "id": "unsafe-strcpy",
        "severity": "high",
        "score": 9,
        "pattern": re.compile(r"\bstrcpy\s*\("),
        "message": "Potential buffer overflow risk with strcpy.",
        "category": "Buffer Overflow",
    },
    {
        "id": "unsafe-strcat",
        "severity": "high",
        "score": 8,
        "pattern": re.compile(r"\bstrcat\s*\("),
        "message": "Potential buffer overflow risk with strcat.",
        "category": "Buffer Overflow",
    },
    {
        "id": "unsafe-sprintf",
        "severity": "high",
        "score": 8,
        "pattern": re.compile(r"\b(v?sn?printf|sprintf|vsprintf)\s*\("),
        "message": "Potential format/string overflow risk with sprintf-family.",
        "category": "Memory Corruption",
    },
    {
        "id": "dangerous-gets",
        "severity": "critical",
        "score": 10,
        "pattern": re.compile(r"\bgets\s*\("),
        "message": "Unsafe input function gets detected.",
        "category": "Buffer Overflow",
    },
    {
        "id": "command-exec",
        "severity": "high",
        "score": 8,
        "pattern": re.compile(r"\b(system|popen|Runtime\.getRuntime\(\)\.exec)\s*\("),
        "message": "Command execution entry point detected.",
        "category": "Command Injection",
    },
    {
        "id": "raw-memcpy",
        "severity": "medium",
        "score": 5,
        "pattern": re.compile(r"\bmemcpy\s*\("),
        "message": "Raw memory copy requires strict boundary checks.",
        "category": "Memory Safety",
    },
    {
        "id": "todo-fixme",
        "severity": "low",
        "score": 2,
        "pattern": re.compile(r"\b(TODO|FIXME)\b"),
        "message": "Unresolved TODO/FIXME marker.",
        "category": "Quality Debt",
    },
    {
        "id": "hardcoded-win-path",
        "severity": "medium",
        "score": 4,
        "pattern": re.compile(r"[A-Za-z]:\\\\"),
        "message": "Hardcoded Windows path detected.",
        "category": "Deployment Fragility",
    },
]


def _is_excluded(path: Path, excludes: list[str]) -> bool:
    return any(part in excludes for part in path.parts)


def _is_comment_line(stripped: str) -> bool:
    return stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*") or stripped.startswith("#")


def scan_risks(config: AnalysisConfig) -> dict[str, Any]:
    project = config.normalized_project_path()
    excludes = config.exclude
    allowed_exts = config.normalized_code_extensions()

    findings: list[dict[str, Any]] = []
    file_scores: dict[str, int] = defaultdict(int)
    rule_counts: dict[str, int] = defaultdict(int)
    category_counts: dict[str, int] = defaultdict(int)

    for path in project.rglob("*"):
        if _is_excluded(path, excludes):
            continue
        if not path.is_file():
            continue
        if config.code_only and path.suffix.lower() not in allowed_exts:
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        rel_path = str(path.relative_to(project)).replace("\\", "/")
        for line_no, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue

            for rule in RISK_RULES:
                if _is_comment_line(stripped) and rule["id"] != "todo-fixme":
                    continue
                if rule["pattern"].search(line):
                    finding = {
                        "file": rel_path,
                        "line": line_no,
                        "rule_id": rule["id"],
                        "severity": rule["severity"],
                        "score": rule["score"],
                        "category": rule["category"],
                        "message": rule["message"],
                        "code": stripped[:220],
                    }
                    findings.append(finding)
                    file_scores[rel_path] += int(rule["score"])
                    rule_counts[rule["id"]] += 1
                    category_counts[rule["category"]] += 1

    heatmap = [
        {
            "file": file,
            "risk_score": score,
            "risk_level": _score_to_level(score),
        }
        for file, score in sorted(file_scores.items(), key=lambda x: x[1], reverse=True)
    ]

    return {
        "findings": findings,
        "heatmap": heatmap,
        "summary": {
            "total_findings": len(findings),
            "files_with_risk": len(file_scores),
            "rule_counts": dict(sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)),
            "category_counts": dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True)),
        },
    }


def _score_to_level(score: int) -> str:
    if score >= 60:
        return "critical"
    if score >= 30:
        return "high"
    if score >= 12:
        return "medium"
    return "low"
