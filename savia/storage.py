"""
Persistencia local + worker de escritura.

Contenido previsto:
  - schema           : tablas readings, hourly_aggregates, sensor_meta
  - open_db()        : sqlite3 connection en modo WAL
  - run_writer_thread: drena readings_queue → INSERT batch
  - aggregate_hourly : tarea periódica que rellena hourly_aggregates
  - retention        : purga datos > 48h

Un único writer thread evita locks de SQLite. Lecturas (uplink, BLE
sync) van por conexiones aparte en modo WAL → concurrencia ok.
"""
