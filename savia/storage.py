"""
Persistencia local SQLite.

Por ahora expone primitivas funcionales (open, init_schema, insert,
purge). El writer thread que drena la `readings` queue se cablea en
una iteración posterior junto con `sensors`.

Diseño: una conexión por hilo. WAL habilitado para permitir lecturas
concurrentes desde uplink/BLE mientras el writer inserta.
"""

import sqlite3
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from savia.types import Reading

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
