from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_EXCLUDES = [".git", "node_modules", "dist", "build", ".venv", "__pycache__"]


@dataclass
class AnalysisConfig:
    project_path: str
    engine: str = "emerge"
    language: str = "auto"
    exclude: list[str] = field(default_factory=lambda: DEFAULT_EXCLUDES.copy())
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

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "AnalysisConfig":
        merged = {
            "exclude": DEFAULT_EXCLUDES.copy(),
            "open_browser": False,
            "fail_on_engine_error": False,
            "locale": "ko",
            **raw,
        }
        if "project_path" not in merged:
            raise ValueError("project_path is required")
        return cls(**merged)
