"""Tests for pipewatch.reaper."""

from datetime import datetime, timedelta

import pytest

from pipewatch.reaper import MetricReaper, ReaperConfig, ReapResult
from pipewatch.history import MetricHistory, HistoryEntry
from pipewatch.metrics import MetricStatus, PipelineMetric, MetricEvaluation


def _make_entry(status: MetricStatus, minutes_ago: float = 0.0) -> HistoryEntry:
    metric = PipelineMetric(name="test", value=1.0)
    evaluation = MetricEvaluation(metric=metric, status=status)
    entry = HistoryEntry(evaluation=evaluation)
    entry.timestamp = datetime.utcnow() - timedelta(minutes=minutes_ago)
    return entry


def make_history(*statuses, minutes_ago: float = 0.0) -> MetricHistory:
    h = MetricHistory(max_entries=100)
    for s in statuses:
        h.record(_make_entry(s, minutes_ago=minutes_ago))
    return h


def make_reaper(**kwargs) -> MetricReaper:
    return MetricReaper(config=ReaperConfig(**kwargs))


def test_evaluate_empty_history_returns_none():
    reaper = make_reaper()
    h = MetricHistory(max_entries=10)
    assert reaper.evaluate("m", h) is None


def test_no_reap_when_ok_and_recent():
    reaper = make_reaper(critical_streak=3, inactive_seconds=3600)
    h = make_history(MetricStatus.OK, MetricStatus.OK)
    assert reaper.evaluate("m", h) is None


def test_critical_streak_triggers_reap():
    reaper = make_reaper(critical_streak=3, inactive_seconds=3600)
    h = make_history(
        MetricStatus.CRITICAL,
        MetricStatus.CRITICAL,
        MetricStatus.CRITICAL,
    )
    result = reaper.evaluate("pipeline.x", h)
    assert result is not None
    assert result.reason == "critical_streak"
    assert result.metric_name == "pipeline.x"


def test_critical_streak_below_threshold_no_reap():
    reaper = make_reaper(critical_streak=5, inactive_seconds=3600)
    h = make_history(
        MetricStatus.CRITICAL,
        MetricStatus.CRITICAL,
        MetricStatus.OK,
    )
    assert reaper.evaluate("m", h) is None


def test_inactive_metric_triggers_reap():
    reaper = make_reaper(critical_streak=10, inactive_seconds=60)
    h = make_history(MetricStatus.OK, minutes_ago=5)  # 5 minutes = 300s > 60s
    result = reaper.evaluate("stale.metric", h)
    assert result is not None
    assert result.reason == "inactive"


def test_inactive_check_takes_priority_over_streak():
    reaper = make_reaper(critical_streak=2, inactive_seconds=60)
    h = MetricHistory(max_entries=10)
    # Two critical entries that are also stale
    h.record(_make_entry(MetricStatus.CRITICAL, minutes_ago=10))
    h.record(_make_entry(MetricStatus.CRITICAL, minutes_ago=5))
    result = reaper.evaluate("m", h)
    assert result is not None
    assert result.reason == "inactive"  # inactivity checked first


def test_evaluate_all_returns_only_reaped():
    reaper = make_reaper(critical_streak=2, inactive_seconds=3600)
    histories = {
        "ok_metric": make_history(MetricStatus.OK, MetricStatus.OK),
        "bad_metric": make_history(MetricStatus.CRITICAL, MetricStatus.CRITICAL),
    }
    results = reaper.evaluate_all(histories)
    assert len(results) == 1
    assert results[0].metric_name == "bad_metric"


def test_reaped_property_accumulates_results():
    reaper = make_reaper(critical_streak=1, inactive_seconds=3600)
    h = make_history(MetricStatus.CRITICAL)
    reaper.evaluate("m1", h)
    reaper.evaluate("m2", h)
    assert len(reaper.reaped) == 2


def test_reap_result_to_dict_has_expected_keys():
    reaper = make_reaper(critical_streak=1, inactive_seconds=3600)
    h = make_history(MetricStatus.CRITICAL)
    result = reaper.evaluate("m", h)
    d = result.to_dict()
    assert "metric_name" in d
    assert "reason" in d
    assert "reaped_at" in d
