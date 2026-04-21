"""Tests for pipewatch.drift."""

from datetime import datetime, timezone
import pytest
from pipewatch.drift import MetricDriftDetector, DriftResult
from pipewatch.history import MetricHistory
from pipewatch.metrics import PipelineMetric
from pipewatch.thresholds import ThresholdEvaluator


def make_history(values: list, name: str = "cpu") -> MetricHistory:
    hist = MetricHistory(max_entries=100)
    evaluator = ThresholdEvaluator(warning=50.0, critical=80.0)
    for v in values:
        metric = PipelineMetric(name=name, value=v)
        evaluation = evaluator.evaluate(metric)
        hist.record(evaluation)
    return hist


def make_detector(**kwargs) -> MetricDriftDetector:
    return MetricDriftDetector(baseline_size=5, recent_size=3, threshold_pct=20.0, **kwargs)


def test_returns_none_when_insufficient_data():
    hist = make_history([10.0, 20.0, 30.0])  # fewer than baseline+recent
    detector = make_detector()
    result = detector.detect("cpu", hist)
    assert result is None


def test_returns_none_when_exactly_baseline_size():
    hist = make_history([10.0] * 5)
    detector = make_detector()
    result = detector.detect("cpu", hist)
    assert result is None


def test_no_drift_when_values_are_stable():
    values = [10.0] * 8  # baseline=5, recent=3 → all same
    hist = make_history(values)
    detector = make_detector()
    result = detector.detect("cpu", hist)
    assert result is not None
    assert result.is_drifting is False
    assert result.drift_percent == pytest.approx(0.0)


def test_drift_detected_when_values_shift_significantly():
    baseline = [10.0] * 5
    recent = [40.0] * 3  # 300% increase
    hist = make_history(baseline + recent)
    detector = make_detector()
    result = detector.detect("cpu", hist)
    assert result is not None
    assert result.is_drifting is True
    assert result.drift_percent > 20.0


def test_drift_result_to_dict_has_expected_keys():
    baseline = [10.0] * 5
    recent = [50.0] * 3
    hist = make_history(baseline + recent)
    detector = make_detector()
    result = detector.detect("cpu", hist)
    assert result is not None
    d = result.to_dict()
    for key in ("metric_name", "baseline_avg", "recent_avg", "drift_absolute", "drift_percent", "is_drifting"):
        assert key in d


def test_drift_absolute_sign_reflects_direction():
    baseline = [20.0] * 5
    recent = [10.0] * 3  # values dropped
    hist = make_history(baseline + recent)
    detector = make_detector(threshold_pct=5.0)
    result = detector.detect("cpu", hist)
    assert result is not None
    assert result.drift_absolute < 0  # recent < baseline


def test_metric_name_preserved_in_result():
    hist = make_history([5.0] * 8, name="latency")
    detector = make_detector()
    result = detector.detect("latency", hist)
    assert result is not None
    assert result.metric_name == "latency"
