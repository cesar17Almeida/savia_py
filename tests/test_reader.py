import logging
import threading
import time

from savia.events import AppEvents
from savia.sensors import DEFAULT_DEPTHS_CM, MockSDI12Probe, run_sensor_loop

CYCLE_SIZE = 2 * len(DEFAULT_DEPTHS_CM)  # 12 readings por ciclo


def _spawn(target, *args, **kwargs):
    t = threading.Thread(target=target, args=args, kwargs=kwargs, daemon=True)
    t.start()
    return t


def test_reader_enqueues_full_cycles():
    events = AppEvents()
    probe = MockSDI12Probe(port=1, seed=0)
    t = _spawn(run_sensor_loop, probe, events, 0.01)
    time.sleep(0.1)
    events.stop.set()
    t.join(timeout=2.0)
    assert not t.is_alive()
    drained = []
    while not events.readings.empty():
        drained.append(events.readings.get_nowait())
    assert len(drained) > 0
    assert len(drained) % CYCLE_SIZE == 0


def test_reader_continues_after_sensor_error(caplog):
    events = AppEvents()
    probe = MockSDI12Probe(port=2, fail_rate=1.0, seed=0)
    with caplog.at_level(logging.WARNING, logger="savia.sensors"):
        t = _spawn(run_sensor_loop, probe, events, 0.01)
        time.sleep(0.05)
        events.stop.set()
        t.join(timeout=2.0)
    assert not t.is_alive()
    assert events.readings.empty()
    assert "measure failed" in caplog.text


def test_reader_stops_promptly_during_period_wait():
    """El stop_event debe interrumpir un wait largo (no esperar el periodo)."""
    events = AppEvents()
    probe = MockSDI12Probe(port=1, seed=0)
    t = _spawn(run_sensor_loop, probe, events, period_s=10.0)
    time.sleep(0.05)
    start = time.monotonic()
    events.stop.set()
    t.join(timeout=2.0)
    elapsed = time.monotonic() - start
    assert not t.is_alive()
    assert elapsed < 1.0
