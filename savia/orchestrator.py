"""
Orquestador asyncio.

Es la corutina que se ejecuta con asyncio.run() desde main(). Lanza
y supervisa las tareas event-driven:
  - ble.run_peripheral()
  - lora.run_uplink_scheduler()
  - supervisor.run()

Maneja señales del SO (SIGTERM/SIGINT) → set stop_event → cancelación
ordenada de tareas y cierre de recursos.
"""
