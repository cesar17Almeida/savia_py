from datetime import datetime

from savia.events import AppEvents
from savia.types import Reading


def test_fresh_events_have_clear_stop_and_empty_queue():
    ev = AppEvents()
    assert not ev.stop.is_set()
    assert ev.readings.empty()


def test_stop_event_set_and_cleared():
    ev = AppEvents()
    ev.stop.set()
    assert ev.stop.is_set()
    ev.stop.clear()
    assert not ev.stop.is_set()


def test_readings_queue_roundtrip():
    ev = AppEvents()
    r = Reading(port=1, kind="soil_moisture", value=0.42, timestamp=datetime(2026, 5, 14, 12, 0, 0))
    ev.readings.put(r)
    out = ev.readings.get_nowait()
    assert out == r


def test_two_instances_are_independent():
    a = AppEvents()
    b = AppEvents()
    a.stop.set()
    assert not b.stop.is_set()
    a.readings.put(Reading(1, "k", 1.0, datetime.now()))
    assert b.readings.empty()
