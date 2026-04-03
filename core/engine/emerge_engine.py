from __future__ import annotations

import json
import shutil
import subprocess
from collections import Counter
from pathlib import Path

from core.config.schema import AnalysisConfig
from core.engine.base import EngineBase, EngineResult


class EmergeEngine(EngineBase):
    name = "emerge"

    def analyze(self, config: AnalysisConfig, run_dir: Path) -> EngineResult:
        project = config.normalized_project_path()
        output_dir = run_dir / "emerge_output"
        output_dir.mkdir(parents=True, exist_ok=True)

        executable = config.emerge_command[0] if config.emerge_command else "emerge"
        if shutil.which(executable) is None:
            fallback = self._local_structure_fallback(project, run_dir, config.exclude)
            fallback.warnings.insert(
                0,
                "Emerge executable not found. Local fallback analysis was used.",
            )
            return fallback

        command = [
            *config.emerge_command,
            "-p",
            str(project),
            "-o",
            str(output_dir),
            *config.emerge_args,
        ]
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        result = EngineResult(
            engine_name=self.name,
            success=proc.returncode == 0,
            command=command,
            stdout=proc.stdout,
            stderr=proc.stderr,
            artifacts={"engine_output": str(output_dir)},
        )

        if proc.returncode != 0:
            result.warnings.append(
                f"Emerge failed with exit code {proc.returncode}. See run log for stderr details."
            )
            if not config.fail_on_engine_error:
                fallback = self._local_structure_fallback(project, run_dir, config.exclude)
                fallback.warnings = result.warnings + fallback.warnings
                fallback.command = command
                fallback.stdout = proc.stdout
                fallback.stderr = proc.stderr
                return fallback

        return result

    def _local_structure_fallback(self, project: Path, run_dir: Path, excludes: list[str]) -> EngineResult:
        excluded = set(excludes)
        file_count = 0
        dir_count = 0
        total_size = 0
        ext_counter: Counter[str] = Counter()

        for path in project.rglob("*"):
            if any(part in excluded for part in path.parts):
                continue
            if path.is_dir():
                dir_count += 1
                continue
            file_count += 1
            total_size += path.stat().st_size
            ext_counter[path.suffix.lower() or "<no_ext>"] += 1

        summary = {
            "project": str(project),
            "file_count": file_count,
            "directory_count": dir_count,
            "total_bytes": total_size,
            "top_extensions": ext_counter.most_common(20),
        }
        summary_path = run_dir / "fallback_summary.json"
        summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

        return EngineResult(
            engine_name="filesystem-fallback",
            success=True,
            artifacts={"fallback_summary": str(summary_path)},
            metrics=summary,
            warnings=["Fallback mode does not generate dependency graphs."],
        )
