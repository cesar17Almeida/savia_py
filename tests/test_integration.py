"""
Tests de integración del pipeline sensor → queue → storage.

Cubre dos niveles:
  - síncrono (test_mock_readings_flow_through_queue_into_storage)
  - con threads reales (test_threaded_pipeline_*) que ejercitan
    run_sensor_loop + run_writer_loop concurrentemente.
"""

import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from savia import storage
from savia.events import AppEvents
from savia.sensors import DEFAULT_DEPTHS_CM, MockSDI12Probe, run_sensor_loop
from savia.storage import run_writer_loop

CYCLE_SIZE = 2 * len(DEFAULT_DEPTHS_CM)


def test_mock_readings_flow_through_queue_into_storage():
    events = AppEvents()
    probe = MockSDI12Probe(port=1, seed=42)

    for r in probe.measure(now=datetime(2026, 5, 14, 12, 0, tzinfo=timezone.utc)):
        events.readings.put(r)

    drained = []
    while not events.readings.empty():
        drained.append(events.readings.get_nowait())
    assert len(drained) == 2 * len(DEFAULT_DEPTHS_CM)

    conn = storage.open_db(":memory:")
    storage.init_schema(conn)
    inserted = storage.insert_readings(conn, drained)
    assert inserted == len(drained)

    moisture_count = conn.execute(
        "SELECT COUNT(*) FROM readings WHERE kind='soil_moisture'"
    ).fetchone()[0]
    temp_count = conn.execute(
        "SELECT COUNT(*) FROM readings WHERE kind='soil_temperature'"
    ).fetchone()[0]
    assert moisture_count == len(DEFAULT_DEPTHS_CM)
    assert temp_count == len(DEFAULT_DEPTHS_CM)
    conn.close()


def test_threaded_pipeline_end_to_end(tmp_path: Path):
    """Reader thread + writer thread coordinados por AppEvents."""
    db = tmp_path / "savia.db"
    conn = storage.open_db(db)
    storage.init_schema(conn)
    conn.close()

    events = AppEvents()
    probe = MockSDI12Probe(port=1, seed=42)

    reader = threading.Thread(
        target=run_sensor_loop,
        args=(probe, events, 0.01),
        daemon=True,
    )
    writer = threading.Thread(
        target=run_writer_loop,
        kwargs={"db_path": db, "events": events, "batch_size": 6, "poll_timeout_s": 0.05},
        daemon=True,
    )
    reader.start()
    writer.start()

    time.sleep(0.2)
    events.stop.set()
    reader.join(timeout=2.0)
    writer.join(timeout=2.0)
    assert not reader.is_alive()
    assert not writer.is_alive()

    conn = storage.open_db(db)
    try:
        count = conn.execute("SELECT COUNT(*) FROM readings").fetchone()[0]
        moisture = conn.execute(
            "SELECT COUNT(*) FROM readings WHERE kind='soil_moisture'"
        ).fetchone()[0]
        temperature = conn.execute(
            "SELECT COUNT(*) FROM readings WHERE kind='soil_temperature'"
        ).fetchone()[0]
    finally:
        conn.close()

    assert count >= CYCLE_SIZE
    assert count % CYCLE_SIZE == 0
    assert moisture == temperature == count // 2
