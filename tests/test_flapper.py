"""Tests for pipewatch.flapper — flap detection."""

from datetime import datetime, timedelta

import pytest

from pipewatch.flapper import FlapDetector, FlapResult
from pipewatch.history import HistoryEntry, MetricHistory
from pipewatch.metrics import MetricStatus


def _make_entry(status: MetricStatus, offset_seconds: int = 0) -> HistoryEntry:
    return HistoryEntry(
        status=status,
        value=1.0,
        timestamp=datetime(2024, 1, 1, 0, 0, 0) + timedelta(seconds=offset_seconds),
    )


def make_history(statuses) -> MetricHistory:
    h = MetricHistory(max_entries=100)
    for i, s in enumerate(statuses):
        h.record(_make_entry(s, offset_seconds=i))
    return h


def make_detector(**kwargs) -> FlapDetector:
    return FlapDetector(**kwargs)


def test_returns_none_for_single_entry():
    h = make_history([MetricStatus.OK])
    result = make_detector().detect("m", h)
    assert result is None


def test_returns_none_for_empty_history():
    h = MetricHistory(max_entries=100)
    result = make_detector().detect("m", h)
    assert result is None


def test_no_flap_when_stable():
    h = make_history([MetricStatus.OK] * 10)
    result = make_detector().detect("m", h)
    assert result is not None
    assert result.is_flapping is False
    assert result.transition_count == 0


def test_flap_detected_on_alternating_statuses():
    statuses = [MetricStatus.OK, MetricStatus.WARNING] * 5
    h = make_history(statuses)
    result = make_detector(window=10, threshold=0.4).detect("m", h)
    assert result is not None
    assert result.is_flapping is True
    assert result.transition_count == 9


def test_flap_rate_calculated_correctly():
    # 2 transitions in 4 entries → rate = 0.5
    statuses = [MetricStatus.OK, MetricStatus.WARNING, MetricStatus.OK, MetricStatus.OK]
    h = make_history(statuses)
    result = make_detector(window=10, threshold=0.4).detect("m", h)
    assert result is not None
    assert result.transition_count == 2
    assert abs(result.flap_rate - 0.5) < 1e-6


def test_threshold_boundary_not_flapping():
    # 1 transition in 5 entries → rate = 0.2, below 0.4
    statuses = [MetricStatus.OK, MetricStatus.WARNING] + [MetricStatus.WARNING] * 3
    h = make_history(statuses)
    result = make_detector(window=10, threshold=0.4).detect("m", h)
    assert result is not None
    assert result.is_flapping is False


def test_events_capture_transitions():
    statuses = [MetricStatus.OK, MetricStatus.CRITICAL, MetricStatus.OK]
    h = make_history(statuses)
    result = make_detector(window=10, threshold=0.1).detect("m", h)
    assert result is not None
    assert len(result.events) == 2
    assert result.events[0].from_status == MetricStatus.OK
    assert result.events[0].to_status == MetricStatus.CRITICAL


def test_to_dict_has_expected_keys():
    statuses = [MetricStatus.OK, MetricStatus.WARNING, MetricStatus.OK]
    h = make_history(statuses)
    result = make_detector(window=10, threshold=0.1).detect("pipe.metric", h)
    assert result is not None
    d = result.to_dict()
    assert "metric_name" in d
    assert "is_flapping" in d
    assert "transition_count" in d
    assert "flap_rate" in d
    assert "events" in d
    assert d["metric_name"] == "pipe.metric"
