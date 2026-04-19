"""Tests for pipewatch.pipeline_status."""

import pytest
from pipewatch.metrics import MetricStatus, PipelineMetric, MetricEvaluation
from pipewatch.pipeline_status import PipelineStatus, evaluate_pipeline


def make_evaluation(name: str, value: float, status: MetricStatus) -> MetricEvaluation:
    metric = PipelineMetric(name=name, value=value)
    return MetricEvaluation(metric=metric, status=status)


def test_overall_ok_when_all_ok():
    ps = evaluate_pipeline("pipe", [
        make_evaluation("a", 1.0, MetricStatus.OK),
        make_evaluation("b", 2.0, MetricStatus.OK),
    ])
    assert ps.overall_status == MetricStatus.OK


def test_overall_warning_when_any_warning():
    ps = evaluate_pipeline("pipe", [
        make_evaluation("a", 1.0, MetricStatus.OK),
        make_evaluation("b", 2.0, MetricStatus.WARNING),
    ])
    assert ps.overall_status == MetricStatus.WARNING


def test_overall_critical_takes_priority():
    ps = evaluate_pipeline("pipe", [
        make_evaluation("a", 1.0, MetricStatus.WARNING),
        make_evaluation("b", 2.0, MetricStatus.CRITICAL),
    ])
    assert ps.overall_status == MetricStatus.CRITICAL


def test_critical_metrics_filtered():
    ps = evaluate_pipeline("pipe", [
        make_evaluation("a", 1.0, MetricStatus.OK),
        make_evaluation("b", 2.0, MetricStatus.CRITICAL),
        make_evaluation("c", 3.0, MetricStatus.CRITICAL),
    ])
    assert len(ps.critical_metrics) == 2
    assert all(e.status == MetricStatus.CRITICAL for e in ps.critical_metrics)


def test_warning_metrics_filtered():
    ps = evaluate_pipeline("pipe", [
        make_evaluation("a", 1.0, MetricStatus.WARNING),
        make_evaluation("b", 2.0, MetricStatus.OK),
    ])
    assert len(ps.warning_metrics) == 1


def test_summary_contains_pipeline_name():
    ps = evaluate_pipeline("my-pipeline", [
        make_evaluation("x", 0.5, MetricStatus.OK),
    ])
    assert "my-pipeline" in ps.summary()


def test_to_dict_structure():
    ps = evaluate_pipeline("pipe", [
        make_evaluation("m1", 10.0, MetricStatus.OK),
        make_evaluation("m2", 20.0, MetricStatus.WARNING),
    ])
    d = ps.to_dict()
    assert d["pipeline"] == "pipe"
    assert d["total"] == 2
    assert d["ok"] == 1
    assert d["warning"] == 1
    assert d["critical"] == 0
    assert len(d["metrics"]) == 2
