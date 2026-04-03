from __future__ import annotations

import argparse
from pathlib import Path

from core.config.loader import load_config
from core.config.schema import AnalysisConfig
from core.runner.analyze import run_analysis


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="codeviz-local",
        description="Local codebase structure analyzer (non-web mode)",
        epilog="Contact: swh@speefox.com | 제작자: 신우혁",
    )
    parser.add_argument("--config", type=str, default="configs/default.yaml", help="Path to config YAML/JSON")
    parser.add_argument("--project", type=str, help="Override project_path")
    parser.add_argument("--engine", type=str, choices=["emerge", "madge", "codecharta"], help="Override engine")
    parser.add_argument("--language", type=str, help="Override language")
    parser.add_argument("--locale", type=str, choices=["ko", "en"], help="UI/Log locale option")
    return parser.parse_args()


def apply_overrides(config: AnalysisConfig, args: argparse.Namespace) -> AnalysisConfig:
    if args.project:
        config.project_path = args.project
    if args.engine:
        config.engine = args.engine
    if args.language:
        config.language = args.language
    if args.locale:
        config.locale = args.locale
    return config


def main() -> int:
    args = parse_args()
    workspace_root = Path(__file__).resolve().parents[2]
    config = load_config(Path(args.config))
    config = apply_overrides(config, args)

    run_dir = run_analysis(config=config, workspace_root=workspace_root)
    print(f"[codeviz-local] run completed: {run_dir}")
    print(f"[codeviz-local] summary: {run_dir / 'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
