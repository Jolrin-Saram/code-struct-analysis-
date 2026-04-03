from __future__ import annotations

from pathlib import Path

from core.config.schema import AnalysisConfig
from core.engine.base import EngineBase, EngineResult


class CodeChartaEngine(EngineBase):
    name = "codecharta"

    def analyze(self, config: AnalysisConfig, run_dir: Path) -> EngineResult:
        return EngineResult(
            engine_name=self.name,
            success=False,
            warnings=["CodeCharta engine is reserved for future feature branch: feature/heatmap-metrics."],
            artifacts={},
        )
