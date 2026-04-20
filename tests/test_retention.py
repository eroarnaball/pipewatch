"""Tests for pipewatch.retention."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from pipewatch.history import MetricHistory, HistoryEntry
from pipewatch.metrics import MetricStatus, PipelineMetric, MetricEvaluation
from pipewatch.retention import RetentionPolicy, RetentionManager, PruneResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_entry(seconds_ago: int, value: float = 1.0) -> HistoryEntry:
    metric = PipelineMetric(name="m", value=value, unit="ms")
    ev = MetricEvaluation(metric=metric, status=MetricStatus.OK, message="ok")
    entry = HistoryEntry(evaluation=ev)
    entry.timestamp = datetime.utcnow() - timedelta(seconds=seconds_ago)
    return entry


def _make_history(*ages: int) -> MetricHistory:
    hist = MetricHistory(max_entries=500)
    hist.entries = [_make_entry(a) for a in ages]
    return hist


# ---------------------------------------------------------------------------
# RetentionPolicy
# ---------------------------------------------------------------------------

def test_default_ttl_used_when_no_override():
    policy = RetentionPolicy(default_ttl_seconds=3600)
    assert policy.ttl_for("any_metric") == 3600


def test_per_metric_ttl_overrides_default():
    policy = RetentionPolicy(
        default_ttl_seconds=3600,
        per_metric_ttl={"special": 600},
    )
    assert policy.ttl_for("special") == 600
    assert policy.ttl_for("other") == 3600


def test_to_dict_contains_expected_keys():
    policy = RetentionPolicy(default_ttl_seconds=7200, per_metric_ttl={"x": 60})
    d = policy.to_dict()
    assert d["default_ttl_seconds"] == 7200
    assert d["per_metric_ttl"] == {"x": 60}


# ---------------------------------------------------------------------------
# RetentionManager.prune
# ---------------------------------------------------------------------------

def test_prune_removes_old_entries():
    hist = _make_history(100, 200, 90000)  # last one is 25 h old
    manager = RetentionManager(RetentionPolicy(default_ttl_seconds=86400))
    result = manager.prune("m", hist)
    assert result.removed == 1
    assert result.remaining == 2


def test_prune_keeps_all_fresh_entries():
    hist = _make_history(10, 20, 30)
    manager = RetentionManager(RetentionPolicy(default_ttl_seconds=86400))
    result = manager.prune("m", hist)
    assert result.removed == 0
    assert result.remaining == 3


def test_prune_removes_all_stale_entries():
    hist = _make_history(7200, 14400)  # both > 1 h
    manager = RetentionManager(RetentionPolicy(default_ttl_seconds=3600))
    result = manager.prune("m", hist)
    assert result.removed == 2
    assert result.remaining == 0


def test_prune_result_metric_name():
    hist = _make_history(50)
    manager = RetentionManager(RetentionPolicy(default_ttl_seconds=86400))
    result = manager.prune("latency", hist)
    assert result.metric_name == "latency"


# ---------------------------------------------------------------------------
# RetentionManager.prune_all
# ---------------------------------------------------------------------------

def test_prune_all_returns_one_result_per_history():
    histories = {
        "a": _make_history(10, 90000),
        "b": _make_history(20),
    }
    manager = RetentionManager(RetentionPolicy(default_ttl_seconds=86400))
    results = manager.prune_all(histories)
    assert len(results) == 2
    names = {r.metric_name for r in results}
    assert names == {"a", "b"}


def test_prune_result_to_dict_keys():
    result = PruneResult(metric_name="x", removed=3, remaining=7)
    d = result.to_dict()
    assert set(d.keys()) == {"metric_name", "removed", "remaining"}
