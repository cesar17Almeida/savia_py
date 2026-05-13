"""Lógica de aplicación de Savia (mínima por ahora)."""

import logging

logger = logging.getLogger(__name__)


def greet(name: str = "world") -> str:
    return f"Hello, {name}!"


def run() -> None:
    logger.info(greet("Savia"))
