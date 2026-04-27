"""Tests for cascade failure detection."""

import pytest
from pipewatch.cascade import CascadeDetector, CascadeResult, CascadeNode
from pipewatch.metrics import MetricStatus, PipelineMetric, MetricEvaluation


def _ev(name: str, status: MetricStatus, value: float = 1.0) -> MetricEvaluation:
    m = PipelineMetric(name=name, value=value, unit="count")
    return MetricEvaluation(metric=m, status=status, message=f"{name}:{status.value}")


def make_detector() -> CascadeDetector:
    d = CascadeDetector()
    d.register_dependency("transform", "ingest")
    d.register_dependency("load", "transform")
    return d


def test_detect_returns_none_when_all_ok():
    detector = make_detector()
    evs = [_ev("ingest", MetricStatus.OK), _ev("transform", MetricStatus.OK)]
    assert detector.detect(evs) is None


def test_detect_returns_none_for_empty_list():
    detector = make_detector()
    assert detector.detect([]) is None


def test_single_failing_metric_is_not_cascade():
    detector = make_detector()
    evs = [
        _ev("ingest", MetricStatus.CRITICAL),
        _ev("transform", MetricStatus.OK),
        _ev("load", MetricStatus.OK),
    ]
    result = detector.detect(evs)
    assert result is not None
    assert result.root_cause == "ingest"
    assert result.is_cascade() is False


def test_cascade_identifies_root_cause():
    detector = make_detector()
    evs = [
        _ev("ingest", MetricStatus.CRITICAL),
        _ev("transform", MetricStatus.CRITICAL),
        _ev("load", MetricStatus.WARNING),
    ]
    result = detector.detect(evs)
    assert result is not None
    assert result.root_cause == "ingest"


def test_cascade_is_true_when_multiple_affected():
    detector = make_detector()
    evs = [
        _ev("ingest", MetricStatus.CRITICAL),
        _ev("transform", MetricStatus.CRITICAL),
    ]
    result = detector.detect(evs)
    assert result is not None
    assert result.is_cascade() is True


def test_cascade_depth_increases_with_chain():
    detector = CascadeDetector()
    detector.register_dependency("b", "a")
    detector.register_dependency("c", "b")
    evs = [
        _ev("a", MetricStatus.CRITICAL),
        _ev("b", MetricStatus.CRITICAL),
        _ev("c", MetricStatus.CRITICAL),
    ]
    result = detector.detect(evs)
    assert result is not None
    assert result.depth >= 2


def test_to_dict_has_expected_keys():
    detector = make_detector()
    evs = [
        _ev("ingest", MetricStatus.CRITICAL),
        _ev("transform", MetricStatus.CRITICAL),
    ]
    result = detector.detect(evs)
    assert result is not None
    d = result.to_dict()
    assert "root_cause" in d
    assert "depth" in d
    assert "is_cascade" in d
    assert "affected" in d
    assert isinstance(d["affected"], list)


def test_cascade_node_to_dict():
    node = CascadeNode(metric_name="transform", status=MetricStatus.CRITICAL, triggered_by="ingest")
    d = node.to_dict()
    assert d["metric_name"] == "transform"
    assert d["status"] == "critical"
    assert d["triggered_by"] == "ingest"
