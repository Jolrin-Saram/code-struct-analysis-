from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def append_run_history(history_path: Path, payload: dict[str, Any]) -> None:
    history_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(payload, ensure_ascii=False)
    with history_path.open("a", encoding="utf-8") as fp:
        fp.write(line + "\n")


def timestamp_id(now: datetime | None = None) -> str:
    now = now or datetime.now()
    return now.strftime("%Y%m%d_%H%M%S")
