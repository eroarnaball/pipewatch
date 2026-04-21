"""Tests for the sliding window aggregator."""

from datetime import datetime, timedelta

import pytest

from pipewatch.history import HistoryEntry, MetricHistory
from pipewatch.metrics import MetricStatus
from pipewatch.window_aggregator import WindowAggregator


def make_history(entries):
    h = MetricHistory(max_entries=200)
    for e in entries:
        h.record(e)
    return h


def make_entry(name, status, value, seconds_ago):
    return HistoryEntry(
        metric_name=name,
        status=status,
        value=float(value),
        timestamp=datetime.utcnow() - timedelta(seconds=seconds_ago),
    )


def test_returns_none_for_unknown_metric():
    history = make_history([])
    agg = WindowAggregator(window_seconds=300)
    result = agg.compute("nonexistent", history)
    assert result is None


def test_empty_window_returns_zero_counts():
    entry = make_entry("m", MetricStatus.OK, 5.0, seconds_ago=600)
    history = make_history([entry])
    agg = WindowAggregator(window_seconds=60)
    result = agg.compute("m", history)
    assert result is not None
    assert result.count == 0
    assert result.ok_count == 0
    assert result.avg_value is None


def test_counts_all_statuses_in_window():
    entries = [
        make_entry("m", MetricStatus.OK, 1.0, seconds_ago=10),
        make_entry("m", MetricStatus.WARNING, 2.0, seconds_ago=20),
        make_entry("m", MetricStatus.CRITICAL, 3.0, seconds_ago=30),
    ]
    history = make_history(entries)
    agg = WindowAggregator(window_seconds=300)
    result = agg.compute("m", history)
    assert result.count == 3
    assert result.ok_count == 1
    assert result.warning_count == 1
    assert result.critical_count == 1


def test_excludes_entries_outside_window():
    entries = [
        make_entry("m", MetricStatus.OK, 1.0, seconds_ago=10),
        make_entry("m", MetricStatus.CRITICAL, 99.0, seconds_ago=500),
    ]
    history = make_history(entries)
    agg = WindowAggregator(window_seconds=60)
    result = agg.compute("m", history)
    assert result.count == 1
    assert result.critical_count == 0


def test_avg_min_max_calculated_correctly():
    entries = [
        make_entry("m", MetricStatus.OK, 10.0, seconds_ago=5),
        make_entry("m", MetricStatus.OK, 20.0, seconds_ago=10),
        make_entry("m", MetricStatus.OK, 30.0, seconds_ago=15),
    ]
    history = make_history(entries)
    agg = WindowAggregator(window_seconds=300)
    result = agg.compute("m", history)
    assert result.avg_value == pytest.approx(20.0)
    assert result.min_value == pytest.approx(10.0)
    assert result.max_value == pytest.approx(30.0)


def test_to_dict_has_expected_keys():
    entry = make_entry("m", MetricStatus.OK, 5.0, seconds_ago=10)
    history = make_history([entry])
    agg = WindowAggregator(window_seconds=300)
    result = agg.compute("m", history)
    d = result.to_dict()
    expected_keys = {
        "metric_name", "window_seconds", "count",
        "ok_count", "warning_count", "critical_count",
        "avg_value", "min_value", "max_value",
    }
    assert expected_keys.issubset(d.keys())
