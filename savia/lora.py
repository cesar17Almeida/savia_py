"""
LoRaWAN / TTN uplink.

Contenido previsto:
  - TTN MQTT client (paho-mqtt) hablando con el broker de TTN
  - run_uplink_scheduler() : cada N min lee agregados horarios de
                              storage, los serializa (CBOR/CayenneLPP)
                              y publica al uplink topic
  - bandwidth detection    : ajusta cadencia según fair-use observado
  - downlink handler       : recibe órdenes del cloud (ej. "ejecuta
                              modelo X") y dispara ml.runner

Tarea asyncio. Frecuencia de envío baja (minutos), no necesita hilo.
"""
