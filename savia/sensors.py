"""
Sensores (drivers + mocks).

Por ahora solo expone `MockSDI12Probe`, que emula el contrato de la
sonda SDI-12 multiprofundidad usada en `research/humidityprobe3/`:
una sonda con 6 puntos de medida, cada ciclo produce 6 valores de
humedad de suelo y 6 de temperatura de suelo (12 Readings total).

El driver SDI-12 real (pyserial, 1200 7E1, break) entrará en una
iteración posterior con la misma interfaz pública `measure()`, de
modo que el resto del firmware (reader thread, storage) no se entera
de si está leyendo hardware o mock.
"""

import logging
import random
from collections.abc import Sequence
from datetime import datetime, timezone

from savia.events import AppEvents
from savia.types import Reading

logger = logging.getLogger(__name__)

DEFAULT_DEPTHS_CM: tuple[int, ...] = (10, 20, 30, 40, 50, 60)

HUMIDITY_RANGE_PCT: tuple[float, float] = (15.0, 45.0)
TEMPERATURE_RANGE_C: tuple[float, float] = (10.0, 28.0)


class SensorError(RuntimeError):
    """El sensor reportó Measure_ERROR o falló la transacción SDI-12."""


class MockSDI12Probe:
    """
    Sonda SDI-12 simulada equivalente a la del .ino de referencia.

    Cada `measure()` devuelve `2 * len(depths_cm)` Readings:
      - `kind="soil_moisture"` (%), una por profundidad
      - `kind="soil_temperature"` (°C), una por profundidad

    Si `fail_rate > 0`, una fracción de las llamadas lanza
    `SensorError` para ejercitar las rutas de manejo de error del
    reader thread.
    """

    def __init__(
        self,
        port: int,
        depths_cm: Sequence[int] = DEFAULT_DEPTHS_CM,
        *,
        fail_rate: float = 0.0,
        seed: int | None = None,
    ) -> None:
        if not 0.0 <= fail_rate <= 1.0:
            raise ValueError(f"fail_rate must be in [0, 1], got {fail_rate}")
        if not depths_cm:
            raise ValueError("depths_cm cannot be empty")
        self.port = port
        self.depths_cm = tuple(depths_cm)
        self.fail_rate = fail_rate
        self._rng = random.Random(seed)

    def measure(self, now: datetime | None = None) -> list[Reading]:
        if self._rng.random() < self.fail_rate:
            raise SensorError(f"port {self.port}: simulated Measure_ERROR")
        ts = now if now is not None else datetime.now(timezone.utc)
        readings: list[Reading] = []
        for depth in self.depths_cm:
            readings.append(
                Reading(
                    port=self.port,
                    kind="soil_moisture",
                    value=self._rng.uniform(*HUMIDITY_RANGE_PCT),
                    timestamp=ts,
                    depth_cm=depth,
                )
            )
        for depth in self.depths_cm:
            readings.append(
                Reading(
                    port=self.port,
                    kind="soil_temperature",
                    value=self._rng.uniform(*TEMPERATURE_RANGE_C),
                    timestamp=ts,
                    depth_cm=depth,
                )
            )
        return readings


def run_sensor_loop(
    probe: MockSDI12Probe,
    events: AppEvents,
    period_s: float,
) -> None:
    """
    Bucle de lectura para correr en un threading.Thread.

    Pide `probe.measure()`, empuja cada Reading a `events.readings` y
    duerme `period_s` segundos antes del siguiente ciclo. Sale en
    cuanto `events.stop` se activa (sin esperar el periodo completo).

    `SensorError` se loguea como warning y se continúa — un fallo
    puntual de lectura no tumba el firmware.
    """
    logger.info("sensor loop start: port=%d period=%.2fs", probe.port, period_s)
    while not events.stop.is_set():
        try:
            readings = probe.measure()
        except SensorError as exc:
            logger.warning("port=%d measure failed: %s", probe.port, exc)
        else:
            for r in readings:
                events.readings.put(r)
            logger.debug("port=%d enqueued %d readings", probe.port, len(readings))
        if events.stop.wait(timeout=period_s):
            break
    logger.info("sensor loop stop: port=%d", probe.port)
