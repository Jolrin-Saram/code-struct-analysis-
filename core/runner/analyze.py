from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Callable

from core.config.schema import AnalysisConfig
from core.engine.codecharta_engine import CodeChartaEngine
from core.engine.emerge_engine import EmergeEngine
from core.engine.madge_engine import MadgeEngine
from core.logging.logger import build_logger
from core.runner.flowchart import build_error_flowchart, summarize_flow_edges
from core.runner.report import append_run_history, timestamp_id, write_json
from core.runner.risk_scan import scan_risks
from core.runner.validate import build_warnings


ProgressCallback = Callable[[str, float], None]


def _engine_map():
    return {
        "emerge": EmergeEngine(),
        "madge": MadgeEngine(),
        "codecharta": CodeChartaEngine(),
    }


def _emit(progress_callback: ProgressCallback | None, message: str, percent: float) -> None:
    if progress_callback:
        clipped = max(0.0, min(100.0, percent))
        progress_callback(message, clipped)


def _phase_progress(
    progress_callback: ProgressCallback | None,
    start: float,
    end: float,
    ratio: float,
    message: str,
) -> None:
    pct = start + ((end - start) * max(0.0, min(1.0, ratio)))
    _emit(progress_callback, message, pct)


def run_analysis(
    config: AnalysisConfig,
    workspace_root: Path,
    progress_callback: ProgressCallback | None = None,
) -> Path:
    _emit(progress_callback, "Validating input paths", 3)
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
    _emit(progress_callback, "Preparing run directory", 8)

    logger = build_logger(run_dir / "run.log")
    logger.info("Analysis started")
    logger.info("Project path: %s", project_path)
    logger.info("Engine: %s", config.engine)

    engines = _engine_map()
    if config.engine not in engines:
        raise ValueError(f"Unsupported engine: {config.engine}")

    engine = engines[config.engine]
    _emit(progress_callback, f"Running engine: {config.engine}", 20)
    engine_result = engine.analyze(config, run_dir)

    _emit(progress_callback, "Scanning static warnings", 30)
    static_warnings = build_warnings(
        config,
        progress_callback=lambda ratio, msg: _phase_progress(progress_callback, 30, 55, ratio, msg),
    )

    _emit(progress_callback, "Scanning risk patterns", 55)
    risk_report = scan_risks(
        config,
        progress_callback=lambda ratio, msg: _phase_progress(progress_callback, 55, 85, ratio, msg),
    )
    risk_summary = risk_report["summary"]

    _emit(progress_callback, "Building risk flowchart", 88)
    flowchart_text = build_error_flowchart(risk_report["findings"])
    flow_edges = summarize_flow_edges(risk_report["findings"])

    combined_warnings = static_warnings + engine_result.warnings
    if risk_summary["total_findings"] > 0:
        combined_warnings.append(
            f"Risk findings detected: {risk_summary['total_findings']} across {risk_summary['files_with_risk']} files."
        )

    artifacts = dict(engine_result.artifacts)
    artifacts["risk_findings"] = str(run_dir / "risk_findings.json")
    artifacts["risk_heatmap"] = str(run_dir / "risk_heatmap.json")
    artifacts["risk_flowchart"] = str(run_dir / "risk_flowchart.mmd")

    payload = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "project_path": str(project_path),
        "engine_requested": config.engine,
        "engine_used": engine_result.engine_name,
        "success": engine_result.success,
        "warnings": combined_warnings,
        "risk_summary": risk_summary,
        "risk_flow_edges": flow_edges,
        "artifacts": artifacts,
        "metrics": engine_result.metrics,
        "command": engine_result.command,
        "stdout_tail": engine_result.stdout[-2000:],
        "stderr_tail": engine_result.stderr[-2000:],
    }

    _emit(progress_callback, "Writing reports", 93)
    write_json(run_dir / "summary.json", payload)
    write_json(run_dir / "warnings.json", {"warnings": payload["warnings"]})
    write_json(run_dir / "risk_findings.json", {"findings": risk_report["findings"]})
    write_json(run_dir / "risk_heatmap.json", {"heatmap": risk_report["heatmap"]})
    (run_dir / "risk_flowchart.mmd").write_text(flowchart_text, encoding="utf-8")

    append_run_history(outputs_root / "run_history.jsonl", payload)

    latest_dir = configured_latest
    latest_dir.mkdir(parents=True, exist_ok=True)
    write_json(latest_dir / "summary.json", payload)
    (latest_dir / "latest_run.txt").write_text(run_id, encoding="utf-8")
    write_json(latest_dir / "risk_findings.json", {"findings": risk_report["findings"]})
    write_json(latest_dir / "risk_heatmap.json", {"heatmap": risk_report["heatmap"]})
    (latest_dir / "risk_flowchart.mmd").write_text(flowchart_text, encoding="utf-8")

    logger.info("Warnings: %s", len(payload["warnings"]))
    logger.info("Risk findings: %s", risk_summary["total_findings"])
    logger.info("Analysis completed. Run directory: %s", run_dir)

    _emit(progress_callback, "Completed", 100)
    return run_dir


def safe_copy_to_latest(run_dir: Path, workspace_root: Path) -> None:
    latest_run_dir = workspace_root / "outputs" / "latest" / "run_copy"
    if latest_run_dir.exists():
        shutil.rmtree(latest_run_dir)
    shutil.copytree(run_dir, latest_run_dir)
