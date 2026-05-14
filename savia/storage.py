"""
Persistencia local SQLite.

Por ahora expone primitivas funcionales (open, init_schema, insert,
purge). El writer thread que drena la `readings` queue se cablea en
una iteración posterior junto con `sensors`.

Diseño: una conexión por hilo. WAL habilitado para permitir lecturas
concurrentes desde uplink/BLE mientras el writer inserta.
"""

import logging
import queue
import sqlite3
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from savia.events import AppEvents
from savia.types import Reading

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS readings (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ts        TEXT    NOT NULL,
    port      INTEGER NOT NULL,
    kind      TEXT    NOT NULL,
    value     REAL    NOT NULL,
    depth_cm  INTEGER
);

CREATE INDEX IF NOT EXISTS idx_readings_ts ON readings(ts);
"""


def open_db(path: Path | str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def insert_readings(conn: sqlite3.Connection, readings: Iterable[Reading]) -> int:
    rows = [
        (r.timestamp.isoformat(), r.port, r.kind, r.value, r.depth_cm)
        for r in readings
    ]
    if not rows:
        return 0
    conn.executemany(
        "INSERT INTO readings (ts, port, kind, value, depth_cm) VALUES (?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    return len(rows)


def purge_older_than(conn: sqlite3.Connection, cutoff: datetime) -> int:
    cur = conn.execute("DELETE FROM readings WHERE ts < ?", (cutoff.isoformat(),))
    conn.commit()
    return cur.rowcount


def run_writer_loop(
    db_path: Path | str,
    events: AppEvents,
    *,
    batch_size: int = 20,
    poll_timeout_s: float = 1.0,
) -> None:
    """
    Drena `events.readings` y persiste en SQLite en batches.

    La conexión se abre dentro de la función — sqlite3 connections
    solo son seguras en el hilo que las crea. El llamador es
    responsable de haber inicializado el schema previamente
    (`init_schema`); aquí asumimos que la tabla `readings` existe.

    Termina cuando `events.stop` está activo Y la queue está vacía,
    garantizando que ninguna lectura encolada antes del shutdown se
    pierde.
    """
    conn = open_db(db_path)
    try:
        logger.info("writer loop start: db=%s batch_size=%d", db_path, batch_size)
        batch: list[Reading] = []
        while not events.stop.is_set() or not events.readings.empty():
            try:
                r = events.readings.get(timeout=poll_timeout_s)
            except queue.Empty:
                if batch:
                    insert_readings(conn, batch)
                    logger.debug("flushed partial batch of %d", len(batch))
                    batch.clear()
                continue
            batch.append(r)
            if len(batch) >= batch_size:
                insert_readings(conn, batch)
                logger.debug("flushed batch of %d", len(batch))
                batch.clear()
        if batch:
            insert_readings(conn, batch)
            logger.debug("final flush of %d", len(batch))
        logger.info("writer loop stop")
    finally:
        conn.close()
