"""Tests for pipewatch.comparator."""

import pytest
from pipewatch.comparator import compare_snapshots, MetricDiff, SnapshotComparison
from pipewatch.snapshot import PipelineSnapshot, MetricSnapshot
from pipewatch.metrics import MetricStatus


def make_snapshot(*metrics: MetricSnapshot) -> PipelineSnapshot:
    snap = PipelineSnapshot()
    for m in metrics:
        snap.add(m)
    return snap


def make_metric(name: str, value: float, status: MetricStatus) -> MetricSnapshot:
    return MetricSnapshot(name=name, value=value, status=status, timestamp=0.0)


def test_no_changes_when_snapshots_identical():
    m = make_metric("latency", 1.0, MetricStatus.OK)
    result = compare_snapshots(make_snapshot(m), make_snapshot(m))
    assert not result.has_changes
    assert result.added == []
    assert result.removed == []


def test_detects_added_metric():
    prev = make_snapshot(make_metric("latency", 1.0, MetricStatus.OK))
    curr = make_snapshot(
        make_metric("latency", 1.0, MetricStatus.OK),
        make_metric("errors", 5.0, MetricStatus.WARNING),
    )
    result = compare_snapshots(prev, curr)
    assert "errors" in result.added
    assert result.has_changes


def test_detects_removed_metric():
    prev = make_snapshot(
        make_metric("latency", 1.0, MetricStatus.OK),
        make_metric("errors", 5.0, MetricStatus.WARNING),
    )
    curr = make_snapshot(make_metric("latency", 1.0, MetricStatus.OK))
    result = compare_snapshots(prev, curr)
    assert "errors" in result.removed
    assert result.has_changes


def test_detects_status_change():
    prev = make_snapshot(make_metric("latency", 1.0, MetricStatus.OK))
    curr = make_snapshot(make_metric("latency", 9.0, MetricStatus.CRITICAL))
    result = compare_snapshots(prev, curr)
    assert result.has_changes
    changed = result.changed_diffs()
    assert len(changed) == 1
    assert changed[0].name == "latency"
    assert changed[0].previous_status == MetricStatus.OK
    assert changed[0].current_status == MetricStatus.CRITICAL


def test_value_delta_computed_correctly():
    prev = make_snapshot(make_metric("latency", 2.0, MetricStatus.OK))
    curr = make_snapshot(make_metric("latency", 5.5, MetricStatus.WARNING))
    result = compare_snapshots(prev, curr)
    assert result.diffs[0].value_delta == pytest.approx(3.5)


def test_to_dict_structure():
    prev = make_snapshot(make_metric("latency", 1.0, MetricStatus.OK))
    curr = make_snapshot(make_metric("latency", 9.0, MetricStatus.CRITICAL))
    d = compare_snapshots(prev, curr).to_dict()
    assert "added" in d
    assert "removed" in d
    assert "diffs" in d
    assert "has_changes" in d
    assert d["diffs"][0]["status_changed"] is True
