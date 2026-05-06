"""
Watchdog de hilos y tareas.

Detecta:
  - threads colgados (sin progreso en N segundos)
  - tareas asyncio que crashean
  - desconexiones BLE o MQTT prolongadas

Acción: log estructurado + intento de reinicio del componente, o
escalada (set stop_event) si el fallo es irrecuperable.
"""
