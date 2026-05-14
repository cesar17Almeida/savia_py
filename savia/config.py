"""
Configuración de la aplicación.

Carga desde TOML con `tomllib` (stdlib) y valida con pydantic. Si no se
pasa path, se usan defaults razonables para desarrollo. En despliegue
real, pasar `--config /etc/savia/config.toml`.
"""

import tomllib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class StorageConfig(BaseModel):
    model_config = {"extra": "forbid"}

    db_path: Path = Path("./savia.db")
    retention_hours: int = Field(default=48, ge=1)


class AppConfig(BaseModel):
    model_config = {"extra": "forbid"}

    log_level: LogLevel = "INFO"
    storage: StorageConfig = Field(default_factory=StorageConfig)


def load(path: Path | None = None) -> AppConfig:
    if path is None:
        return AppConfig()
    with path.open("rb") as f:
        data = tomllib.load(f)
    return AppConfig.model_validate(data)
