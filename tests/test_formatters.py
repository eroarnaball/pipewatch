"""Tests for output formatters."""

import json
import pytest
from pipewatch.formatters import format_table, format_json, format_summary
from pipewatch.metrics import MetricEvaluation, MetricStatus, PipelineMetric


def make_ev(pipeline, name, value, status, message=""):
    metric = PipelineMetric(pipeline=pipeline, name=name, value=value)
    return MetricEvaluation(metric=metric, status=status, message=message)


EVALUATIONS = [
    make_ev("pipe1", "row_count", 1000.0, MetricStatus.OK),
    make_ev("pipe1", "null_rate", 0.15, MetricStatus.WARNING, "Above warning"),
    make_ev("pipe2", "latency", 95.0, MetricStatus.CRITICAL, "Too slow"),
]


def test_format_table_contains_headers():
    output = format_table(EVALUATIONS, color=False)
    assert "PIPELINE" in output
    assert "METRIC" in output
    assert "STATUS" in output


def test_format_table_contains_values():
    output = format_table(EVALUATIONS, color=False)
    assert "pipe1" in output
    assert "row_count" in output
    assert "WARNING" in output
    assert "CRITICAL" in output


def test_format_json_valid():
    output = format_json(EVALUATIONS)
    data = json.loads(output)
    assert len(data) == 3
    assert data[0]["pipeline"] == "pipe1"
    assert data[2]["status"] == "critical"


def test_format_json_structure():
    output = format_json(EVALUATIONS)
    data = json.loads(output)
    for item in data:
        assert "pipeline" in item
        assert "metric" in item
        assert "value" in item
        assert "status" in item


def test_format_summary_counts():
    summary = format_summary(EVALUATIONS)
    assert "Total: 3" in summary
    assert "OK: 1" in summary
    assert "WARNING: 1" in summary
    assert "CRITICAL: 1" in summary


def test_format_summary_all_ok():
    evs = [make_ev("p", "m", 1.0, MetricStatus.OK) for _ in range(3)]
    summary = format_summary(evs)
    assert "CRITICAL: 0" in summary
    assert "WARNING: 0" in summary
