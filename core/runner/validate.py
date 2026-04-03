from __future__ import annotations

import re
from pathlib import Path

from core.config.schema import AnalysisConfig


SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)api[_-]?key\s*[:=]\s*['\"][^'\"]+['\"]"),
    re.compile(r"(?i)password\s*[:=]\s*['\"][^'\"]+['\"]"),
]


def _is_excluded(path: Path, excludes: list[str]) -> bool:
    return any(part in excludes for part in path.parts)


def _is_code_file(path: Path, config: AnalysisConfig) -> bool:
    if not path.is_file():
        return False
    if not config.code_only:
        return True
    return path.suffix.lower() in config.normalized_code_extensions()


def build_warnings(config: AnalysisConfig) -> list[str]:
    project = config.normalized_project_path()
    excludes = config.exclude
    warnings: list[str] = []

    if not (project / "README.md").exists() and not (project / "README.MD").exists():
        warnings.append("README file not found. Project entry documentation is missing.")

    tests_exists = any((project / name).exists() for name in ["tests", "test", "__tests__"])
    if not tests_exists:
        warnings.append("No common test directory detected (tests/test/__tests__).")

    max_depth = 0
    large_file_threshold = config.warning_max_file_size_mb * 1024 * 1024

    for path in project.rglob("*"):
        if _is_excluded(path, excludes):
            continue

        rel_depth = len(path.relative_to(project).parts)
        max_depth = max(max_depth, rel_depth)

        if not _is_code_file(path, config):
            continue

        try:
            size = path.stat().st_size
        except OSError:
            continue

        if size > large_file_threshold:
            warnings.append(
                f"Large code file detected: {path} ({size / (1024 * 1024):.2f} MB)."
            )

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        if "TODO" in content or "FIXME" in content:
            warnings.append(f"TODO/FIXME marker found: {path}")

        for pattern in SECRET_PATTERNS:
            if pattern.search(content):
                warnings.append(f"Potential secret pattern found: {path}")
                break

    if max_depth > config.warning_max_directory_depth:
        warnings.append(
            f"Directory depth is {max_depth}, exceeding threshold {config.warning_max_directory_depth}."
        )

    deduped = list(dict.fromkeys(warnings))
    return deduped
