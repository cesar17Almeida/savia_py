"""Lógica de aplicación de Savia (mínima por ahora)."""

import logging

from savia.config import AppConfig

logger = logging.getLogger(__name__)


def greet(name: str = "world") -> str:
    return f"Hello, {name}!"


def run(cfg: AppConfig | None = None) -> None:
    if cfg is None:
        cfg = AppConfig()
    logger.info(greet("Savia"))
    logger.info(
        "Storage: db=%s retention=%dh",
        cfg.storage.db_path,
        cfg.storage.retention_hours,
    )
