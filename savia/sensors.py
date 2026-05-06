"""
Drivers de sensores y hilo de lectura.

Contenido previsto:
  - Reading           : dataclass (port, depth, kind, value, ts)
  - SDI12Bus          : driver bloqueante sobre pyserial (1200 7E1, break)
  - I2CDriver         : wrapper smbus2
  - SPIDriver         : wrapper spidev
  - run_sensor_thread : while not stop_event: por cada bus/dirección,
                        leer → emitir Reading a readings_queue → sleep

Es un hilo nativo (threading.Thread), no asyncio: pyserial bloquea y
es timing-sensitive. Uno por bus físico (un SDI-12 = un bus, no un
hilo por sensor).
"""
