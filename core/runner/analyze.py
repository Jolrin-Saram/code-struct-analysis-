from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from core.config.schema import AnalysisConfig
from core.engine.codecharta_engine import CodeChartaEngine
from core.engine.emerge_engine import EmergeEngine
from core.engine.madge_engine import MadgeEngine
from core.logging.logger import build_logger
from core.runner.report import append_run_history, timestamp_id, write_json
from core.runner.validate import build_warnings


def _engine_map():
    return {
        "emerge": EmergeEngine(),
        "madge": MadgeEngine(),
        "codecharta": CodeChartaEngine(),
    }


def run_analysis(config: AnalysisConfig, workspace_root: Path) -> Path:
    project_path = config.normalized_project_path()
    if not project_path.exists() or not project_path.is_dir():
        raise ValueError(f"Invalid project_path: {project_path}")

    configured_latest = Path(config.output_dir)
    if not configured_latest.is_absolute():
        configured_latest = (workspace_root / configured_latest).resolve()

    outputs_root = configured_latest.parent
    runs_root = outputs_root / "runs"
    run_id = timestamp_id()
    run_dir = runs_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    logger = build_logger(run_dir / "run.log")
    logger.info("Analysis started")
    logger.info("Project path: %s", project_path)
    logger.info("Engine: %s", config.engine)

    engines = _engine_map()
    if config.engine not in engines:
        raise ValueError(f"Unsupported engine: {config.engine}")

    engine = engines[config.engine]
    engine_result = engine.analyze(config, run_dir)
    static_warnings = build_warnings(config)

    payload = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "project_path": str(project_path),
        "engine_requested": config.engine,
        "engine_used": engine_result.engine_name,
        "success": engine_result.success,
        "warnings": static_warnings + engine_result.warnings,
        "artifacts": engine_result.artifacts,
        "metrics": engine_result.metrics,
        "command": engine_result.command,
        "stdout_tail": engine_result.stdout[-2000:],
        "stderr_tail": engine_result.stderr[-2000:],
    }

    write_json(run_dir / "summary.json", payload)
    write_json(run_dir / "warnings.json", {"warnings": payload["warnings"]})

    append_run_history(outputs_root / "run_history.jsonl", payload)

    latest_dir = configured_latest
    latest_dir.mkdir(parents=True, exist_ok=True)
    write_json(latest_dir / "summary.json", payload)
    (latest_dir / "latest_run.txt").write_text(run_id, encoding="utf-8")

    logger.info("Warnings: %s", len(payload["warnings"]))
    logger.info("Analysis completed. Run directory: %s", run_dir)

    return run_dir


def safe_copy_to_latest(run_dir: Path, workspace_root: Path) -> None:
    latest_run_dir = workspace_root / "outputs" / "latest" / "run_copy"
    if latest_run_dir.exists():
        shutil.rmtree(latest_run_dir)
    shutil.copytree(run_dir, latest_run_dir)
