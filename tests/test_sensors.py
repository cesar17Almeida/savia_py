from datetime import datetime, timezone

import pytest

from savia.sensors import (
    DEFAULT_DEPTHS_CM,
    HUMIDITY_RANGE_PCT,
    TEMPERATURE_RANGE_C,
    MockSDI12Probe,
    SensorError,
)


def test_measure_returns_two_readings_per_depth():
    probe = MockSDI12Probe(port=1, seed=42)
    readings = probe.measure()
    assert len(readings) == 2 * len(DEFAULT_DEPTHS_CM)


def test_measure_splits_humidity_and_temperature():
    probe = MockSDI12Probe(port=1, seed=42)
    readings = probe.measure()
    kinds = [r.kind for r in readings]
    assert kinds.count("soil_moisture") == len(DEFAULT_DEPTHS_CM)
    assert kinds.count("soil_temperature") == len(DEFAULT_DEPTHS_CM)


def test_each_depth_covered_for_both_kinds():
    probe = MockSDI12Probe(port=3, seed=0)
    readings = probe.measure()
    moisture_depths = sorted(r.depth_cm for r in readings if r.kind == "soil_moisture")
    temp_depths = sorted(r.depth_cm for r in readings if r.kind == "soil_temperature")
    assert moisture_depths == list(DEFAULT_DEPTHS_CM)
    assert temp_depths == list(DEFAULT_DEPTHS_CM)


def test_values_within_expected_range():
    probe = MockSDI12Probe(port=1, seed=123)
    readings = probe.measure()
    for r in readings:
        if r.kind == "soil_moisture":
            assert HUMIDITY_RANGE_PCT[0] <= r.value <= HUMIDITY_RANGE_PCT[1]
        else:
            assert TEMPERATURE_RANGE_C[0] <= r.value <= TEMPERATURE_RANGE_C[1]


def test_same_seed_produces_same_readings():
    a = MockSDI12Probe(port=1, seed=7).measure(datetime(2026, 5, 14, tzinfo=timezone.utc))
    b = MockSDI12Probe(port=1, seed=7).measure(datetime(2026, 5, 14, tzinfo=timezone.utc))
    assert a == b


def test_port_propagates_to_readings():
    probe = MockSDI12Probe(port=5, seed=0)
    readings = probe.measure()
    assert all(r.port == 5 for r in readings)


def test_explicit_timestamp_used():
    ts = datetime(2026, 1, 1, 9, 30, 0, tzinfo=timezone.utc)
    probe = MockSDI12Probe(port=1, seed=0)
    readings = probe.measure(now=ts)
    assert all(r.timestamp == ts for r in readings)


def test_custom_depths():
    probe = MockSDI12Probe(port=1, depths_cm=(15, 45, 90), seed=0)
    readings = probe.measure()
    assert len(readings) == 2 * 3
    assert {r.depth_cm for r in readings} == {15, 45, 90}


def test_fail_rate_one_always_raises():
    probe = MockSDI12Probe(port=1, fail_rate=1.0, seed=0)
    with pytest.raises(SensorError):
        probe.measure()


def test_fail_rate_zero_never_raises():
    probe = MockSDI12Probe(port=1, fail_rate=0.0, seed=0)
    for _ in range(20):
        probe.measure()


def test_invalid_fail_rate_rejected():
    with pytest.raises(ValueError):
        MockSDI12Probe(port=1, fail_rate=1.5)


def test_empty_depths_rejected():
    with pytest.raises(ValueError):
        MockSDI12Probe(port=1, depths_cm=())
