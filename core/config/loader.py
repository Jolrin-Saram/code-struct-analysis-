from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.config.schema import AnalysisConfig


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "YAML config requires PyYAML. Install with: pip install pyyaml"
        ) from exc

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data or {}


def load_config(path: Path) -> AnalysisConfig:
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")

    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        raw = _read_yaml(path)
    elif suffix == ".json":
        raw = json.loads(path.read_text(encoding="utf-8"))
    else:
        raise ValueError(f"Unsupported config format: {suffix}")

    return AnalysisConfig.from_dict(raw)
