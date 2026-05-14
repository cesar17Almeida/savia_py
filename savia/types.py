"""Tipos de dominio compartidos entre módulos."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Reading:
    port: int
    kind: str
    value: float
    timestamp: datetime
    depth_cm: int | None = None
