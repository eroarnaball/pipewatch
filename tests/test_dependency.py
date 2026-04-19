import pytest
from pipewatch.dependency import DependencyGraph, DependencyViolation
from pipewatch.metrics import MetricStatus


def make_graph() -> DependencyGraph:
    g = DependencyGraph()
    g.register("ingest", depends_on=[])
    g.register("transform", depends_on=["ingest"])
    g.register("load", depends_on=["transform"])
    return g


def test_register_and_get_dependencies():
    g = make_graph()
    assert g.get_dependencies("transform") == ["ingest"]
    assert g.get_dependencies("ingest") == []


def test_get_dependencies_unknown_metric():
    g = make_graph()
    assert g.get_dependencies("nonexistent") == []


def test_no_violations_when_all_ok():
    g = make_graph()
    statuses = {
        "ingest": MetricStatus.OK,
        "transform": MetricStatus.OK,
        "load": MetricStatus.OK,
    }
    assert g.check_violations(statuses) == []


def test_violation_when_dependency_critical():
    g = make_graph()
    statuses = {
        "ingest": MetricStatus.CRITICAL,
        "transform": MetricStatus.OK,
        "load": MetricStatus.OK,
    }
    violations = g.check_violations(statuses)
    assert len(violations) == 1
    assert violations[0].metric == "transform"
    assert violations[0].blocked_by == "ingest"


def test_warning_does_not_cause_violation():
    g = make_graph()
    statuses = {
        "ingest": MetricStatus.WARNING,
        "transform": MetricStatus.OK,
        "load": MetricStatus.OK,
    }
    assert g.check_violations(statuses) == []


def test_cascade_violations():
    g = make_graph()
    statuses = {
        "ingest": MetricStatus.CRITICAL,
        "transform": MetricStatus.CRITICAL,
        "load": MetricStatus.OK,
    }
    violations = g.check_violations(statuses)
    metrics = {v.metric for v in violations}
    assert "transform" in metrics
    assert "load" in metrics


def test_topological_order_respects_dependencies():
    g = make_graph()
    order = g.topological_order()
    assert order.index("ingest") < order.index("transform")
    assert order.index("transform") < order.index("load")


def test_violation_to_dict_has_expected_keys():
    v = DependencyViolation(metric="load", blocked_by="transform", reason="test")
    d = v.to_dict()
    assert set(d.keys()) == {"metric", "blocked_by", "reason"}
