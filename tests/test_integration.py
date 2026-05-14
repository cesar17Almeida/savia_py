"""
Smoke test de integración: mock sensor → events.readings → storage.

No es un test funcional completo (no hay reader thread real todavía),
pero verifica que los contratos entre las piezas encajan: el sensor
produce Readings que la queue acepta, que storage persiste y devuelve
sin pérdida.
"""

from datetime import datetime, timezone

from savia import storage
from savia.events import AppEvents
from savia.sensors import DEFAULT_DEPTHS_CM, MockSDI12Probe


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
