"""
Configuración del firmware.

Responsabilidad: cargar y validar la configuración (puertos activos,
mapping sensor→puerto, cadencias, credenciales TTN, parámetros BLE)
desde fichero YAML/TOML + variables de entorno. Expone un objeto
inmutable consumido por el resto de módulos.

Pendiente: definir esquema con pydantic.
"""
