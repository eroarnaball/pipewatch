"""Tests for pipewatch.exporter."""

import csv
import json
from pathlib import Path

import pytest

from pipewatch.exporter import export_csv, export_json, export_report
from pipewatch.metrics import MetricStatus, PipelineMetric
from pipewatch.thresholds import ThresholdEvaluator
from pipewatch.reporter import RunReport


def make_report():
    metrics = [
        PipelineMetric(name="latency", value=120.0, unit="ms"),
        PipelineMetric(name="error_rate", value=0.02, unit="ratio"),
    ]
    evaluator = ThresholdEvaluator(warning=100.0, critical=200.0)
    evaluations = [evaluator.evaluate(m) for m in metrics]
    return RunReport(evaluations=evaluations)


def test_export_json_creates_file(tmp_path):
    out = tmp_path / "report.json"
    export_json(make_report(), out)
    assert out.exists()


def test_export_json_valid_structure(tmp_path):
    out = tmp_path / "report.json"
    export_json(make_report(), out)
    data = json.loads(out.read_text())
    assert "evaluations" in data
    assert isinstance(data["evaluations"], list)
    assert len(data["evaluations"]) == 2


def test_export_csv_creates_file(tmp_path):
    out = tmp_path / "report.csv"
    export_csv(make_report(), out)
    assert out.exists()


def test_export_csv_has_correct_headers(tmp_path):
    out = tmp_path / "report.csv"
    export_csv(make_report(), out)
    reader = csv.DictReader(out.read_text().splitlines())
    assert set(reader.fieldnames) == {"metric", "value", "status", "timestamp"}


def test_export_csv_row_count(tmp_path):
    out = tmp_path / "report.csv"
    export_csv(make_report(), out)
    rows = list(csv.DictReader(out.read_text().splitlines()))
    assert len(rows) == 2


def test_export_report_dispatches_json(tmp_path):
    out = tmp_path / "r.json"
    export_report(make_report(), out, fmt="json")
    assert out.exists()
    json.loads(out.read_text())  # must be valid JSON


def test_export_report_dispatches_csv(tmp_path):
    out = tmp_path / "r.csv"
    export_report(make_report(), out, fmt="csv")
    assert out.exists()


def test_export_report_invalid_format_raises(tmp_path):
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_report(make_report(), tmp_path / "r.xml", fmt="xml")
