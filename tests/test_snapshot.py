"""Tests for pipewatch.snapshot."""

import json

import pytest

from pipewatch.metrics import MetricStatus
from pipewatch.snapshot import MetricSnapshot, PipelineSnapshot


def make_metric_snapshot(name="latency", value=0.5, status=MetricStatus.OK):
    return MetricSnapshot(name=name, value=value, status=status, timestamp="2024-01-01T00:00:00")


def test_metric_snapshot_to_dict():
    s = make_metric_snapshot()
    d = s.to_dict()
    assert d["name"] == "latency"
    assert d["value"] == 0.5
    assert d["status"] == "ok"
    assert d["timestamp"] == "2024-01-01T00:00:00"


def test_metric_snapshot_roundtrip():
    original = make_metric_snapshot(status=MetricStatus.WARNING)
    restored = MetricSnapshot.from_dict(original.to_dict())
    assert restored.name == original.name
    assert restored.value == original.value
    assert restored.status == original.status
    assert restored.timestamp == original.timestamp


def test_pipeline_snapshot_add_and_summary():
    snap = PipelineSnapshot(captured_at="2024-01-01T00:00:00")
    snap.add(make_metric_snapshot(status=MetricStatus.OK))
    snap.add(make_metric_snapshot(name="errors", value=5.0, status=MetricStatus.CRITICAL))
    snap.add(make_metric_snapshot(name="lag", value=2.0, status=MetricStatus.WARNING))
    summary = snap.summary()
    assert summary["ok"] == 1
    assert summary["warning"] == 1
    assert summary["critical"] == 1


def test_pipeline_snapshot_to_json_valid():
    snap = PipelineSnapshot(captured_at="2024-01-01T00:00:00")
    snap.add(make_metric_snapshot())
    raw = snap.to_json()
    data = json.loads(raw)
    assert "captured_at" in data
    assert len(data["metrics"]) == 1


def test_pipeline_snapshot_from_json_roundtrip():
    snap = PipelineSnapshot(captured_at="2024-01-01T00:00:00")
    snap.add(make_metric_snapshot(status=MetricStatus.CRITICAL))
    restored = PipelineSnapshot.from_json(snap.to_json())
    assert restored.captured_at == snap.captured_at
    assert len(restored.metrics) == 1
    assert restored.metrics[0].status == MetricStatus.CRITICAL


def test_pipeline_snapshot_empty_summary():
    snap = PipelineSnapshot()
    summary = snap.summary()
    assert all(v == 0 for v in summary.values())
