"""Tests for pipewatch.baseline module."""

import pytest
from unittest.mock import MagicMock
from pipewatch.baseline import BaselineTracker, BaselineStats, DeviationResult


def make_history(values):
    entries = [MagicMock(value=v) for v in values]
    history = MagicMock()
    history.get_all.return_value = entries
    return history


def test_compute_baseline_insufficient_data():
    tracker = BaselineTracker(min_samples=5)
    history = make_history([1.0, 2.0])
    result = tracker.compute_baseline(history, "latency")
    assert result is None


def test_compute_baseline_returns_stats():
    tracker = BaselineTracker(min_samples=3)
    history = make_history([10.0, 12.0, 11.0, 10.5, 11.5])
    result = tracker.compute_baseline(history, "latency")
    assert isinstance(result, BaselineStats)
    assert result.metric_name == "latency"
    assert result.sample_count == 5
    assert result.mean == pytest.approx(11.0, rel=0.01)
    assert result.stddev > 0


def test_compute_baseline_to_dict_keys():
    tracker = BaselineTracker(min_samples=3)
    history = make_history([10.0, 11.0, 12.0, 10.5, 11.5])
    stats = tracker.compute_baseline(history, "throughput")
    d = stats.to_dict()
    for key in ("metric_name", "sample_count", "mean", "stddev", "lower_bound", "upper_bound"):
        assert key in d


def test_check_deviation_no_anomaly():
    tracker = BaselineTracker(sensitivity=2.0, min_samples=3)
    history = make_history([10.0, 10.0, 10.0, 10.0, 10.0])
    result = tracker.check_deviation(10.0, history, "latency")
    assert isinstance(result, DeviationResult)
    assert not result.is_anomaly


def test_check_deviation_anomaly_detected():
    tracker = BaselineTracker(sensitivity=2.0, min_samples=3)
    history = make_history([10.0, 10.1, 9.9, 10.0, 10.05])
    result = tracker.check_deviation(50.0, history, "latency")
    assert result.is_anomaly
    assert result.z_score is not None
    assert result.z_score > 2.0


def test_check_deviation_insufficient_history_not_anomaly():
    tracker = BaselineTracker(min_samples=10)
    history = make_history([1.0, 2.0])
    result = tracker.check_deviation(999.0, history, "errors")
    assert not result.is_anomaly
    assert result.z_score is None
    assert result.baseline is None


def test_check_deviation_zero_stddev():
    tracker = BaselineTracker(sensitivity=2.0, min_samples=3)
    history = make_history([5.0, 5.0, 5.0, 5.0, 5.0])
    result = tracker.check_deviation(5.0, history, "metric")
    assert not result.is_anomaly
    assert result.z_score == 0.0
