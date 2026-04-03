from __future__ import annotations

from pathlib import Path

from core.config.schema import AnalysisConfig
from core.engine.base import EngineBase, EngineResult


class MadgeEngine(EngineBase):
    name = "madge"

    def analyze(self, config: AnalysisConfig, run_dir: Path) -> EngineResult:
        return EngineResult(
            engine_name=self.name,
            success=False,
            warnings=["Madge engine is reserved for future feature branch: feature/js-fast-mode."],
            artifacts={},
        )
