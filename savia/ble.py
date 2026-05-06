"""
BLE peripheral — comms con TerraLink (app móvil).

Contenido previsto:
  - GATT services    : config, sync, control (UUIDs por definir)
  - run_peripheral() : registra GATT con bluez-peripheral, anuncia,
                       maneja conexiones del central (móvil)
  - file transfer    : chunking sobre notify (v0) → L2CAP CoC (v1)

Corre como tarea asyncio dentro del orchestrator — bluez-peripheral
y dbus-fast están construidos sobre asyncio.

Pieza más frágil del stack: aislar e iterar pronto.
"""
