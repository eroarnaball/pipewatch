"""Tests for pipewatch.history module."""

import json
import os
import tempfile

import pytest

from pipewatch.history import MetricHistory, HistoryEntry
from pipewatch.metrics import PipelineMetric, MetricEvaluation, MetricStatus


def make_evaluation(name="pipeline.lag", value=10.0, status=MetricStatus.OK, message="ok"):
    metric = PipelineMetric(name=name, value=value)
    return MetricEvaluation(metric=metric, status=status, message=message)


def test_record_adds_entry():
    history = MetricHistory()
    ev = make_evaluation()
    entry = history.record(ev)
    assert isinstance(entry, HistoryEntry)
    assert len(history.get_all()) == 1


def test_max_entries_enforced():
    history = MetricHistory(max_entries=3)
    for i in range(5):
        history.record(make_evaluation(value=float(i)))
    assert len(history.get_all()) == 3


def test_get_by_status_filters_correctly():
    history = MetricHistory()
    history.record(make_evaluation(status=MetricStatus.OK))
    history.record(make_evaluation(status=MetricStatus.WARNING))
    history.record(make_evaluation(status=MetricStatus.CRITICAL))
    history.record(make_evaluation(status=MetricStatus.WARNING))

    warnings = history.get_by_status(MetricStatus.WARNING)
    assert len(warnings) == 2
    criticals = history.get_by_status(MetricStatus.CRITICAL)
    assert len(criticals) == 1


def test_entry_to_dict_has_expected_keys():
    ev = make_evaluation(name="rows.count", value=42.0, status=MetricStatus.WARNING)
    entry = HistoryEntry(ev)
    d = entry.to_dict()
    assert d["metric_name"] == "rows.count"
    assert d["value"] == 42.0
    assert d["status"] == MetricStatus.WARNING.value
    assert "timestamp" in d
    assert "message" in d


def test_save_and_load_roundtrip():
    history = MetricHistory()
    history.record(make_evaluation(name="lag", value=5.0, status=MetricStatus.OK))
    history.record(make_evaluation(name="lag", value=95.0, status=MetricStatus.CRITICAL))

    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "history.json")
        history.save(path)

        assert os.path.exists(path)
        with open(path) as f:
            raw = json.load(f)
        assert len(raw) == 2

        history2 = MetricHistory()
        history2.load(path)
        entries = history2.get_all()
        assert len(entries) == 2
        assert entries[1].evaluation.status == MetricStatus.CRITICAL


def test_load_missing_file_is_noop():
    history = MetricHistory()
    history.load("/nonexistent/path/history.json")
    assert history.get_all() == []
