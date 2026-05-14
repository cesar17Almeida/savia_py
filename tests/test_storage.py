import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from savia import storage
from savia.types import Reading


@pytest.fixture
def conn():
    c = storage.open_db(":memory:")
    storage.init_schema(c)
    yield c
    c.close()


def test_open_db_enables_foreign_keys(conn: sqlite3.Connection):
    cur = conn.execute("PRAGMA foreign_keys")
    assert cur.fetchone()[0] == 1


def test_init_schema_is_idempotent(conn: sqlite3.Connection):
    storage.init_schema(conn)
    storage.init_schema(conn)
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='readings'")
    assert cur.fetchone() is not None


def test_insert_and_select_roundtrip(conn: sqlite3.Connection):
    ts = datetime(2026, 5, 14, 12, 0, 0)
    readings = [
        Reading(port=1, kind="soil_moisture", value=0.42, timestamp=ts, depth_cm=20),
        Reading(port=2, kind="temperature", value=18.3, timestamp=ts),
    ]
    n = storage.insert_readings(conn, readings)
    assert n == 2
    rows = conn.execute("SELECT port, kind, value, depth_cm FROM readings ORDER BY port").fetchall()
    assert rows == [(1, "soil_moisture", 0.42, 20), (2, "temperature", 18.3, None)]


def test_insert_empty_iterable_is_noop(conn: sqlite3.Connection):
    assert storage.insert_readings(conn, []) == 0
    count = conn.execute("SELECT COUNT(*) FROM readings").fetchone()[0]
    assert count == 0


def test_purge_older_than_keeps_recent(conn: sqlite3.Connection):
    now = datetime(2026, 5, 14, 12, 0, 0)
    old = now - timedelta(hours=49)
    fresh = now - timedelta(hours=1)
    storage.insert_readings(conn, [
        Reading(1, "k", 1.0, old),
        Reading(1, "k", 2.0, fresh),
    ])
    cutoff = now - timedelta(hours=48)
    deleted = storage.purge_older_than(conn, cutoff)
    assert deleted == 1
    remaining = conn.execute("SELECT value FROM readings").fetchall()
    assert remaining == [(2.0,)]


def test_open_db_creates_file(tmp_path: Path):
    db = tmp_path / "savia.db"
    conn = storage.open_db(db)
    storage.init_schema(conn)
    conn.close()
    assert db.exists()
