"""Tests for pipewatch.grouper."""

import pytest
from pipewatch.metrics import MetricStatus, PipelineMetric, MetricEvaluation
from pipewatch.grouper import MetricGrouper, MetricGroup


def make_evaluation(name: str, status: MetricStatus, value: float = 1.0) -> MetricEvaluation:
    metric = PipelineMetric(name=name, value=value)
    return MetricEvaluation(metric=metric, status=status, message="")


@pytest.fixture
def grouper() -> MetricGrouper:
    return MetricGrouper()


def test_group_by_status_empty(grouper):
    result = grouper.group_by_status([])
    assert result == {}


def test_group_by_status_all_ok(grouper):
    evs = [make_evaluation(f"m{i}", MetricStatus.OK) for i in range(3)]
    result = grouper.group_by_status(evs)
    assert "ok" in result
    assert len(result["ok"].members) == 3
    assert result["ok"].key == "status"


def test_group_by_status_mixed(grouper):
    evs = [
        make_evaluation("a", MetricStatus.OK),
        make_evaluation("b", MetricStatus.WARNING),
        make_evaluation("c", MetricStatus.CRITICAL),
        make_evaluation("d", MetricStatus.WARNING),
    ]
    result = grouper.group_by_status(evs)
    assert len(result["ok"].members) == 1
    assert len(result["warning"].members) == 2
    assert len(result["critical"].members) == 1


def test_group_by_status_member_names(grouper):
    evs = [
        make_evaluation("alpha", MetricStatus.CRITICAL),
        make_evaluation("beta", MetricStatus.CRITICAL),
    ]
    result = grouper.group_by_status(evs)
    assert "alpha" in result["critical"].members
    assert "beta" in result["critical"].members


def test_filter_group_returns_subset(grouper):
    evs = [
        make_evaluation("x", MetricStatus.OK),
        make_evaluation("y", MetricStatus.WARNING),
        make_evaluation("z", MetricStatus.OK),
    ]
    group = MetricGroup(key="status", value="ok", members=["x", "z"])
    filtered = grouper.filter_group(group, evs)
    assert len(filtered) == 2
    names = [ev.metric.name for ev in filtered]
    assert "x" in names
    assert "z" in names
    assert "y" not in names


def test_summary_returns_counts(grouper):
    evs = [
        make_evaluation("a", MetricStatus.OK),
        make_evaluation("b", MetricStatus.OK),
        make_evaluation("c", MetricStatus.WARNING),
    ]
    s = grouper.summary(evs)
    assert s["ok"] == 2
    assert s["warning"] == 1
    assert "critical" not in s


def test_metric_group_to_dict():
    g = MetricGroup(key="status", value="warning", members=["m1", "m2"])
    d = g.to_dict()
    assert d["key"] == "status"
    assert d["value"] == "warning"
    assert d["count"] == 2
    assert "m1" in d["members"]
