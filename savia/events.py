"""
Primitivas de sincronización compartidas entre threads y asyncio.

Contiene:
  - stop_event       : threading.Event global de apagado
  - readings_queue   : queue.Queue para Reading objects (sensor → storage)
  - uplink_signal    : asyncio.Event "hay agregado nuevo listo para LoRa"
  - bridge helpers   : envoltorios sobre janus / call_soon_threadsafe

Toda comunicación entre componentes pasa por aquí — ningún módulo
crea sus propias primitivas globales.
"""
