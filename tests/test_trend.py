"""Tests for pipewatch.trend."""

from unittest.mock import MagicMock
from pipewatch.trend import detect_trend, status_trend, TrendDirection
from pipewatch.history import MetricHistory, HistoryEntry
from pipewatch.metrics import MetricStatus


def make_entry(name, status, value):
    e = MagicMock(spec=HistoryEntry)
    e.metric_name = name
    e.status = status
    e.value = value
    return e


def make_history(entries):
    h = MagicMock(spec=MetricHistory)
    h.entries = entries
    return h


def test_insufficient_data_single_entry():
    h = make_history([make_entry("cpu", MetricStatus.OK, 0.5)])
    assert detect_trend(h, "cpu") == TrendDirection.INSUFFICIENT_DATA


def test_stable_trend_flat_values():
    entries = [make_entry("cpu", MetricStatus.OK, 0.5) for _ in range(5)]
    h = make_history(entries)
    assert detect_trend(h, "cpu") == TrendDirection.STABLE


def test_degrading_trend_rising_values():
    entries = [make_entry("cpu", MetricStatus.OK, float(i)) for i in range(1, 6)]
    h = make_history(entries)
    assert detect_trend(h, "cpu") == TrendDirection.DEGRADING


def test_improving_trend_falling_values():
    entries = [make_entry("cpu", MetricStatus.OK, float(i)) for i in range(5, 0, -1)]
    h = make_history(entries)
    assert detect_trend(h, "cpu") == TrendDirection.IMPROVING


def test_status_trend_degrading():
    entries = [
        make_entry("errors", MetricStatus.OK, 0),
        make_entry("errors", MetricStatus.WARNING, 1),
        make_entry("errors", MetricStatus.CRITICAL, 2),
    ]
    h = make_history(entries)
    assert status_trend(h, "errors") == TrendDirection.DEGRADING


def test_status_trend_improving():
    entries = [
        make_entry("errors", MetricStatus.CRITICAL, 2),
        make_entry("errors", MetricStatus.WARNING, 1),
        make_entry("errors", MetricStatus.OK, 0),
    ]
    h = make_history(entries)
    assert status_trend(h, "errors") == TrendDirection.IMPROVING


def test_status_trend_insufficient():
    h = make_history([])
    assert status_trend(h, "errors") == TrendDirection.INSUFFICIENT_DATA
