"""Tests for pipewatch.rollup."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from pipewatch.rollup import MetricRollup, RollupWindow
from pipewatch.history import MetricHistory, HistoryEntry
from pipewatch.metrics import MetricStatus


def make_history(entries: list[tuple[MetricStatus, float, int]]) -> MetricHistory:
    """entries: list of (status, value, seconds_ago)"""
    history = MetricHistory(max_entries=100)
    now = datetime.utcnow()
    for status, value, secs_ago in entries:
        entry = HistoryEntry(
            metric_name="test_metric",
            status=status,
            value=value,
            timestamp=now - timedelta(seconds=secs_ago),
        )
        history.record(entry)
    return history


def make_rollup(window_seconds: int = 300) -> MetricRollup:
    return MetricRollup(window_seconds=window_seconds)


def test_compute_returns_none_for_unregistered_metric():
    rollup = make_rollup()
    assert rollup.compute("missing") is None


def test_compute_empty_window_returns_zero_counts():
    rollup = make_rollup(window_seconds=60)
    history = make_history([(MetricStatus.OK, 10.0, 120)])  # outside 60s window
    rollup.register("m", history)
    result = rollup.compute("m")
    assert result is not None
    assert result.total == 0
    assert result.ok_count == 0
    assert result.avg_value is None


def test_compute_counts_statuses_correctly():
    rollup = make_rollup(window_seconds=300)
    history = make_history([
        (MetricStatus.OK, 10.0, 10),
        (MetricStatus.WARNING, 20.0, 20),
        (MetricStatus.CRITICAL, 30.0, 30),
        (MetricStatus.OK, 15.0, 40),
    ])
    rollup.register("m", history)
    result = rollup.compute("m")
    assert result.total == 4
    assert result.ok_count == 2
    assert result.warning_count == 1
    assert result.critical_count == 1


def test_compute_calculates_min_max_avg():
    rollup = make_rollup(window_seconds=300)
    history = make_history([
        (MetricStatus.OK, 10.0, 10),
        (MetricStatus.OK, 20.0, 20),
        (MetricStatus.OK, 30.0, 30),
    ])
    rollup.register("m", history)
    result = rollup.compute("m")
    assert result.min_value == pytest.approx(10.0)
    assert result.max_value == pytest.approx(30.0)
    assert result.avg_value == pytest.approx(20.0)


def test_compute_all_returns_all_registered():
    rollup = make_rollup()
    rollup.register("a", make_history([(MetricStatus.OK, 1.0, 5)]))
    rollup.register("b", make_history([(MetricStatus.WARNING, 2.0, 5)]))
    results = rollup.compute_all()
    assert set(results.keys()) == {"a", "b"}


def test_to_dict_has_expected_keys():
    rollup = make_rollup()
    rollup.register("m", make_history([(MetricStatus.OK, 5.0, 10)]))
    result = rollup.compute("m")
    d = result.to_dict()
    for key in ("metric_name", "window_seconds", "start", "end",
                "total", "ok_count", "warning_count", "critical_count",
                "min_value", "max_value", "avg_value"):
        assert key in d


def test_window_seconds_respected():
    rollup = make_rollup(window_seconds=50)
    history = make_history([
        (MetricStatus.OK, 1.0, 10),   # inside
        (MetricStatus.OK, 2.0, 40),   # inside
        (MetricStatus.OK, 3.0, 60),   # outside
    ])
    rollup.register("m", history)
    result = rollup.compute("m")
    assert result.total == 2
