"""Tests for pipewatch.capper."""

import pytest
from pipewatch.capper import MetricCapper


def make_capper() -> MetricCapper:
    return MetricCapper()


def test_register_returns_bounds():
    capper = make_capper()
    bounds = capper.register("cpu", min_value=0.0, max_value=100.0)
    assert bounds.min_value == 0.0
    assert bounds.max_value == 100.0


def test_register_min_only():
    capper = make_capper()
    bounds = capper.register("latency", min_value=0.0)
    assert bounds.min_value == 0.0
    assert bounds.max_value is None


def test_register_max_only():
    capper = make_capper()
    bounds = capper.register("queue", max_value=500.0)
    assert bounds.min_value is None
    assert bounds.max_value == 500.0


def test_register_invalid_range_raises():
    capper = make_capper()
    with pytest.raises(ValueError):
        capper.register("bad", min_value=100.0, max_value=10.0)


def test_cap_within_bounds_not_capped():
    capper = make_capper()
    capper.register("cpu", min_value=0.0, max_value=100.0)
    result = capper.cap("cpu", 55.0)
    assert result.capped == 55.0
    assert result.was_capped is False
    assert result.original == 55.0


def test_cap_above_max_is_clamped():
    capper = make_capper()
    capper.register("cpu", min_value=0.0, max_value=100.0)
    result = capper.cap("cpu", 150.0)
    assert result.capped == 100.0
    assert result.was_capped is True


def test_cap_below_min_is_clamped():
    capper = make_capper()
    capper.register("cpu", min_value=0.0, max_value=100.0)
    result = capper.cap("cpu", -5.0)
    assert result.capped == 0.0
    assert result.was_capped is True


def test_cap_unregistered_metric_passthrough():
    capper = make_capper()
    result = capper.cap("unknown", 42.0)
    assert result.capped == 42.0
    assert result.was_capped is False
    assert result.original == 42.0


def test_cap_at_exact_boundary_not_capped():
    capper = make_capper()
    capper.register("score", min_value=0.0, max_value=1.0)
    result = capper.cap("score", 1.0)
    assert result.capped == 1.0
    assert result.was_capped is False


def test_to_dict_has_expected_keys():
    capper = make_capper()
    bounds = capper.register("mem", min_value=10.0, max_value=90.0)
    d = bounds.to_dict()
    assert "min_value" in d
    assert "max_value" in d


def test_capped_value_to_dict_has_expected_keys():
    capper = make_capper()
    capper.register("cpu", max_value=100.0)
    result = capper.cap("cpu", 200.0)
    d = result.to_dict()
    assert set(d.keys()) == {"metric_name", "original", "capped", "was_capped"}


def test_all_bounds_returns_registered_metrics():
    capper = make_capper()
    capper.register("a", max_value=10.0)
    capper.register("b", min_value=1.0)
    bounds = capper.all_bounds()
    assert "a" in bounds
    assert "b" in bounds
