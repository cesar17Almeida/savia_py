"""
Primitivas de sincronización compartidas entre threads y asyncio.

`AppEvents` agrupa el `stop` global y la `readings` queue. El
orchestrator lo crea una vez y lo inyecta a cada módulo — ningún
módulo instancia primitivas globales por su cuenta.

Cuando entre asyncio (orchestrator + BLE + LoRa), la queue migrará a
`janus.Queue` para puentear thread → asyncio. Por ahora `queue.Queue`
stdlib es suficiente para los productores/consumidores en hilos nativos.
"""

import threading
from dataclasses import dataclass, field
from queue import Queue

from savia.types import Reading


@dataclass(slots=True)
class AppEvents:
    stop: threading.Event = field(default_factory=threading.Event)
    readings: Queue[Reading] = field(default_factory=Queue)
