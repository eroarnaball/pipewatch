"""Tests for threshold evaluation logic."""
import pytest
from pipewatch.metrics import MetricStatus, PipelineMetric
from pipewatch.thresholds import ThresholdEvaluator


def make_metric(value: float, unit: str = None) -> PipelineMetric:
    return PipelineMetric(pipeline_name="test_pipe", metric_name="lag_seconds", value=value, unit=unit)


def test_ok_when_below_warning():
    ev = ThresholdEvaluator(warning=10.0, critical=20.0)
    result = ev.evaluate(make_metric(5.0))
    assert result.status == MetricStatus.OK


def test_warning_when_at_warning_threshold():
    ev = ThresholdEvaluator(warning=10.0, critical=20.0)
    result = ev.evaluate(make_metric(10.0))
    assert result.status == MetricStatus.WARNING


def test_critical_when_at_critical_threshold():
    ev = ThresholdEvaluator(warning=10.0, critical=20.0)
    result = ev.evaluate(make_metric(20.0))
    assert result.status == MetricStatus.CRITICAL


def test_critical_takes_priority_over_warning():
    ev = ThresholdEvaluator(warning=5.0, critical=10.0)
    result = ev.evaluate(make_metric(15.0))
    assert result.status == MetricStatus.CRITICAL


def test_lte_comparator_ok_above_threshold():
    ev = ThresholdEvaluator(warning=5.0, critical=2.0, comparator="lte")
    result = ev.evaluate(make_metric(10.0))
    assert result.status == MetricStatus.OK


def test_lte_comparator_critical_below_threshold():
    ev = ThresholdEvaluator(warning=5.0, critical=2.0, comparator="lte")
    result = ev.evaluate(make_metric(1.0))
    assert result.status == MetricStatus.CRITICAL


def test_no_thresholds_always_ok():
    ev = ThresholdEvaluator()
    result = ev.evaluate(make_metric(999.0))
    assert result.status == MetricStatus.OK


def test_invalid_comparator_raises():
    with pytest.raises(ValueError):
        ThresholdEvaluator(comparator="eq")


def test_message_contains_metric_name():
    ev = ThresholdEvaluator(warning=10.0)
    result = ev.evaluate(make_metric(15.0, unit="s"))
    assert "lag_seconds" in result.message
