import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from savia import storage
from savia.events import AppEvents
from savia.storage import run_writer_loop
from savia.types import Reading


def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "savia.db"
    conn = storage.open_db(db)
    storage.init_schema(conn)
    conn.close()
    return db


def _count_readings(db: Path) -> int:
    conn = storage.open_db(db)
    try:
        return conn.execute("SELECT COUNT(*) FROM readings").fetchone()[0]
    finally:
        conn.close()


def _make_reading(i: int) -> Reading:
    return Reading(
        port=1,
        kind="soil_moisture",
        value=float(i),
        timestamp=datetime(2026, 5, 14, 12, 0, tzinfo=timezone.utc),
    )


def test_writer_persists_full_batches(tmp_path: Path):
    db = _init_db(tmp_path)
    events = AppEvents()
    for i in range(10):
        events.readings.put(_make_reading(i))
    t = threading.Thread(
        target=run_writer_loop,
        kwargs={"db_path": db, "events": events, "batch_size": 4, "poll_timeout_s": 0.05},
        daemon=True,
    )
    t.start()
    time.sleep(0.2)
    events.stop.set()
    t.join(timeout=2.0)
    assert not t.is_alive()
    assert _count_readings(db) == 10


def test_writer_flushes_partial_batch_on_timeout(tmp_path: Path):
    """Con batch_size grande y pocas readings, el timeout fuerza el flush."""
    db = _init_db(tmp_path)
    events = AppEvents()
    for i in range(3):
        events.readings.put(_make_reading(i))
    t = threading.Thread(
        target=run_writer_loop,
        kwargs={"db_path": db, "events": events, "batch_size": 100, "poll_timeout_s": 0.05},
        daemon=True,
    )
    t.start()
    time.sleep(0.2)  # > poll_timeout → debe haber flusheado el batch parcial
    assert _count_readings(db) == 3
    events.stop.set()
    t.join(timeout=2.0)


def test_writer_drains_queue_before_stopping(tmp_path: Path):
    """Readings encoladas justo antes de stop deben persistirse antes de salir."""
    db = _init_db(tmp_path)
    events = AppEvents()
    t = threading.Thread(
        target=run_writer_loop,
        kwargs={"db_path": db, "events": events, "batch_size": 100, "poll_timeout_s": 0.05},
        daemon=True,
    )
    t.start()
    for i in range(5):
        events.readings.put(_make_reading(i))
    events.stop.set()
    t.join(timeout=2.0)
    assert not t.is_alive()
    assert _count_readings(db) == 5


def test_writer_handles_empty_queue_and_immediate_stop(tmp_path: Path):
    db = _init_db(tmp_path)
    events = AppEvents()
    events.stop.set()
    t = threading.Thread(
        target=run_writer_loop,
        kwargs={"db_path": db, "events": events, "poll_timeout_s": 0.05},
        daemon=True,
    )
    t.start()
    t.join(timeout=2.0)
    assert not t.is_alive()
    assert _count_readings(db) == 0
