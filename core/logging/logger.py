from __future__ import annotations

import logging
from pathlib import Path


def build_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("codeviz")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    stream_handler = logging.StreamHandler()

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger
