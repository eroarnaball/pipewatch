"""Tests for pipewatch.anomaly module."""

from unittest.mock import MagicMock
from pipewatch.anomaly import AnomalyDetector, AnomalyReport


def make_history(values):
    entries = [MagicMock(value=v) for v in values]
    history = MagicMock()
    history.get_all.return_value = entries
    return history


def make_evaluation(value, name="latency"):
    metric = MagicMock()
    metric.name = name
    ev = MagicMock()
    ev.value = value
    ev.metric = metric
    return ev


def test_evaluate_returns_none_for_missing_value():
    detector = AnomalyDetector()
    ev = make_evaluation(None)
    history = make_history([1.0, 2.0, 3.0])
    result = detector.evaluate(ev, history)
    assert result is None


def test_evaluate_normal_value_not_anomaly():
    detector = AnomalyDetector(sensitivity=2.0, min_samples=3)
    history = make_history([10.0, 10.0, 10.0, 10.0, 10.0])
    ev = make_evaluation(10.0)
    result = detector.evaluate(ev, history)
    assert result is not None
    assert not result.is_anomaly


def test_evaluate_extreme_value_is_anomaly():
    detector = AnomalyDetector(sensitivity=2.0, min_samples=3)
    history = make_history([10.0, 10.1, 9.9, 10.0, 10.05])
    ev = make_evaluation(999.0)
    result = detector.evaluate(ev, history)
    assert result.is_anomaly


def test_scan_history_returns_report():
    detector = AnomalyDetector(sensitivity=2.0, min_samples=3)
    history = make_history([10.0, 10.0, 10.0, 10.0, 10.0])
    report = detector.scan_history(history, "latency")
    assert isinstance(report, AnomalyReport)
    assert report.metric_name == "latency"


def test_scan_history_detects_no_anomalies_in_stable_data():
    detector = AnomalyDetector(sensitivity=2.0, min_samples=3)
    history = make_history([10.0, 10.0, 10.0, 10.0, 10.0])
    report = detector.scan_history(history, "latency")
    assert not report.has_anomalies


def test_anomaly_report_to_dict_structure():
    detector = AnomalyDetector(sensitivity=2.0, min_samples=3)
    history = make_history([10.0, 10.1, 9.9, 10.0, 10.05])
    report = detector.scan_history(history, "errors")
    d = report.to_dict()
    assert "metric_name" in d
    assert "has_anomalies" in d
    assert "anomaly_count" in d
    assert "results" in d
    assert isinstance(d["results"], list)
