"""Tests for pipewatch.aggregator."""

import pytest
from unittest.mock import MagicMock
from pipewatch.aggregator import MetricAggregator, AggregatedStats
from pipewatch.history import MetricHistory, HistoryEntry
from pipewatch.metrics import MetricStatus
from datetime import datetime


def make_entry(name: str, status: MetricStatus, value: float) -> HistoryEntry:
    entry = MagicMock(spec=HistoryEntry)
    entry.metric_name = name
    entry.status = status
    entry.value = value
    return entry


def make_history(entries):
    history = MagicMock(spec=MetricHistory)
    history.entries = entries
    return history


def test_compute_empty_returns_zero_stats():
    agg = MetricAggregator(make_history([]))
    stats = agg.compute("latency")
    assert stats.total == 0
    assert stats.avg_value is None


def test_compute_counts_statuses():
    entries = [
        make_entry("latency", MetricStatus.OK, 1.0),
        make_entry("latency", MetricStatus.WARNING, 2.0),
        make_entry("latency", MetricStatus.CRITICAL, 3.0),
    ]
    agg = MetricAggregator(make_history(entries))
    stats = agg.compute("latency")
    assert stats.ok_count == 1
    assert stats.warning_count == 1
    assert stats.critical_count == 1
    assert stats.total == 3


def test_compute_calculates_min_max_avg():
    entries = [
        make_entry("latency", MetricStatus.OK, 10.0),
        make_entry("latency", MetricStatus.OK, 20.0),
        make_entry("latency", MetricStatus.OK, 30.0),
    ]
    agg = MetricAggregator(make_history(entries))
    stats = agg.compute("latency")
    assert stats.min_value == 10.0
    assert stats.max_value == 30.0
    assert stats.avg_value == 20.0


def test_compute_all_returns_one_per_metric():
    entries = [
        make_entry("latency", MetricStatus.OK, 1.0),
        make_entry("errors", MetricStatus.WARNING, 5.0),
        make_entry("latency", MetricStatus.OK, 2.0),
    ]
    agg = MetricAggregator(make_history(entries))
    results = agg.compute_all()
    names = [s.metric_name for s in results]
    assert "latency" in names
    assert "errors" in names
    assert len(results) == 2


def test_to_dict_has_expected_keys():
    stats = AggregatedStats(metric_name="cpu", total=2, ok_count=2, min_value=0.1, max_value=0.9, avg_value=0.5)
    d = stats.to_dict()
    for key in ("metric_name", "total", "ok_count", "warning_count", "critical_count", "min_value", "max_value", "avg_value"):
        assert key in d
