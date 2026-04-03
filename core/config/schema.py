from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_EXCLUDES = [
    ".git",
    ".vs",
    ".idea",
    "node_modules",
    "dist",
    "build",
    "bin",
    "obj",
    "out",
    "target",
    ".venv",
    "venv",
    "__pycache__",
    "x64",
    "Debug",
    "Release",
]

# Includes C/C++ headers and Python runtime-related code files.
DEFAULT_CODE_EXTENSIONS = [
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".hh",
    ".hpp",
    ".py",
    ".pyw",
    ".pyi",
    ".pyx",
    ".pxd",
    ".java",
    ".r",
    ".R",
]


@dataclass
class AnalysisConfig:
    project_path: str
    engine: str = "emerge"
    language: str = "auto"
    exclude: list[str] = field(default_factory=lambda: DEFAULT_EXCLUDES.copy())
    code_extensions: list[str] = field(default_factory=lambda: DEFAULT_CODE_EXTENSIONS.copy())
    code_only: bool = True
    output_dir: str = "./outputs/latest"
    open_browser: bool = False
    fail_on_engine_error: bool = False
    locale: str = "ko"
    emerge_command: list[str] = field(default_factory=lambda: ["emerge"])
    emerge_args: list[str] = field(default_factory=list)
    warning_max_file_size_mb: int = 2
    warning_max_directory_depth: int = 8

    def normalized_project_path(self) -> Path:
        return Path(self.project_path).expanduser().resolve()

    def normalized_code_extensions(self) -> set[str]:
        normalized: set[str] = set()
        for ext in self.code_extensions:
            e = ext if ext.startswith(".") else f".{ext}"
            normalized.add(e.lower())
        return normalized

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "AnalysisConfig":
        merged = {
            "exclude": DEFAULT_EXCLUDES.copy(),
            "code_extensions": DEFAULT_CODE_EXTENSIONS.copy(),
            "code_only": True,
            "open_browser": False,
            "fail_on_engine_error": False,
            "locale": "ko",
            **raw,
        }
        if "project_path" not in merged:
            raise ValueError("project_path is required")
        return cls(**merged)
