from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from core.config.schema import AnalysisConfig
from core.engine.codecharta_engine import CodeChartaEngine
from core.engine.emerge_engine import EmergeEngine
from core.engine.madge_engine import MadgeEngine
from core.logging.logger import build_logger
from core.runner.flowchart import build_error_flowchart, summarize_flow_edges
from core.runner.report import append_run_history, timestamp_id, write_json
from core.runner.risk_scan import scan_risks
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
    risk_report = scan_risks(config)
    risk_summary = risk_report["summary"]
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

    return run_dir


def safe_copy_to_latest(run_dir: Path, workspace_root: Path) -> None:
    latest_run_dir = workspace_root / "outputs" / "latest" / "run_copy"
    if latest_run_dir.exists():
        shutil.rmtree(latest_run_dir)
    shutil.copytree(run_dir, latest_run_dir)
