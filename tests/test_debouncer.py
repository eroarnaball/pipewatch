"""Tests for pipewatch.debouncer."""

import pytest
from pipewatch.debouncer import AlertDebouncer, DebounceResult
from pipewatch.metrics import MetricStatus


def make_debouncer(threshold: int = 3) -> AlertDebouncer:
    return AlertDebouncer(threshold=threshold)


def test_ok_status_is_never_suppressed():
    d = make_debouncer(threshold=3)
    result = d.evaluate("latency", MetricStatus.OK)
    assert not result.suppressed
    assert result.status == MetricStatus.OK


def test_first_warning_is_suppressed():
    d = make_debouncer(threshold=3)
    result = d.evaluate("latency", MetricStatus.WARNING)
    assert result.suppressed
    assert result.consecutive_count == 1


def test_warning_below_threshold_remains_suppressed():
    d = make_debouncer(threshold=3)
    d.evaluate("latency", MetricStatus.WARNING)
    result = d.evaluate("latency", MetricStatus.WARNING)
    assert result.suppressed
    assert result.consecutive_count == 2


def test_warning_at_threshold_is_not_suppressed():
    d = make_debouncer(threshold=3)
    d.evaluate("latency", MetricStatus.WARNING)
    d.evaluate("latency", MetricStatus.WARNING)
    result = d.evaluate("latency", MetricStatus.WARNING)
    assert not result.suppressed
    assert result.consecutive_count == 3


def test_warning_beyond_threshold_remains_unsuppressed():
    d = make_debouncer(threshold=2)
    d.evaluate("latency", MetricStatus.WARNING)
    d.evaluate("latency", MetricStatus.WARNING)
    result = d.evaluate("latency", MetricStatus.WARNING)
    assert not result.suppressed
    assert result.consecutive_count == 3


def test_status_change_resets_counter():
    d = make_debouncer(threshold=3)
    d.evaluate("latency", MetricStatus.WARNING)
    d.evaluate("latency", MetricStatus.WARNING)
    # Status changes to CRITICAL — counter resets
    result = d.evaluate("latency", MetricStatus.CRITICAL)
    assert result.suppressed
    assert result.consecutive_count == 1


def test_ok_clears_state():
    d = make_debouncer(threshold=3)
    d.evaluate("latency", MetricStatus.WARNING)
    d.evaluate("latency", MetricStatus.OK)
    assert d.state_for("latency") is None


def test_reset_clears_state():
    d = make_debouncer(threshold=3)
    d.evaluate("latency", MetricStatus.CRITICAL)
    d.reset("latency")
    assert d.state_for("latency") is None


def test_threshold_one_never_suppresses_non_ok():
    d = make_debouncer(threshold=1)
    result = d.evaluate("latency", MetricStatus.CRITICAL)
    assert not result.suppressed


def test_invalid_threshold_raises():
    with pytest.raises(ValueError):
        AlertDebouncer(threshold=0)


def test_to_dict_has_expected_keys():
    d = make_debouncer(threshold=2)
    d.evaluate("cpu", MetricStatus.WARNING)
    result = d.evaluate("cpu", MetricStatus.WARNING)
    data = result.to_dict()
    assert "metric_name" in data
    assert "status" in data
    assert "suppressed" in data
    assert "consecutive_count" in data
    assert "threshold" in data
