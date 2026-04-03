from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.config.schema import AnalysisConfig


@dataclass
class EngineResult:
    engine_name: str
    success: bool
    artifacts: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    command: list[str] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""


class EngineBase:
    name = "base"

    def analyze(
        self,
        config: AnalysisConfig,
        run_dir: Path,
    ) -> EngineResult:
        raise NotImplementedError
