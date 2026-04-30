"""Tests for pipewatch.stamper."""

import time

import pytest

from pipewatch.metrics import MetricEvaluation, MetricStatus, PipelineMetric
from pipewatch.stamper import MetricStamper, StampedEvaluation


def make_evaluation(name: str = "orders", value: float = 10.0, status: MetricStatus = MetricStatus.OK) -> MetricEvaluation:
    metric = PipelineMetric(name=name, value=value)
    return MetricEvaluation(metric=metric, status=status)


@pytest.fixture
def stamper() -> MetricStamper:
    return MetricStamper()


def test_stamp_returns_stamped_evaluation(stamper):
    ev = make_evaluation()
    result = stamper.stamp(ev)
    assert isinstance(result, StampedEvaluation)


def test_stamp_sequence_starts_at_one(stamper):
    ev = make_evaluation()
    result = stamper.stamp(ev)
    assert result.sequence == 1


def test_stamp_sequence_increments_per_metric(stamper):
    ev = make_evaluation(name="latency")
    r1 = stamper.stamp(ev)
    r2 = stamper.stamp(ev)
    r3 = stamper.stamp(ev)
    assert r1.sequence == 1
    assert r2.sequence == 2
    assert r3.sequence == 3


def test_stamp_sequences_are_independent_per_metric(stamper):
    ev_a = make_evaluation(name="a")
    ev_b = make_evaluation(name="b")
    stamper.stamp(ev_a)
    stamper.stamp(ev_a)
    r_b = stamper.stamp(ev_b)
    assert r_b.sequence == 1


def test_stamp_id_is_twelve_hex_chars(stamper):
    ev = make_evaluation()
    result = stamper.stamp(ev)
    assert len(result.stamp_id) == 12
    assert all(c in "0123456789abcdef" for c in result.stamp_id)


def test_stamp_ids_are_unique_across_stamps(stamper):
    ev = make_evaluation()
    ids = {stamper.stamp(ev).stamp_id for _ in range(20)}
    assert len(ids) > 1


def test_history_for_returns_all_stamps(stamper):
    ev = make_evaluation(name="throughput")
    stamper.stamp(ev)
    stamper.stamp(ev)
    stamper.stamp(ev)
    history = stamper.history_for("throughput")
    assert len(history) == 3


def test_history_for_unknown_returns_empty(stamper):
    assert stamper.history_for("nonexistent") == []


def test_latest_returns_most_recent(stamper):
    ev = make_evaluation(name="errors")
    stamper.stamp(ev)
    last = stamper.stamp(ev)
    assert stamper.latest("errors") is last


def test_latest_returns_none_for_unknown(stamper):
    assert stamper.latest("ghost") is None


def test_all_names_lists_stamped_metrics(stamper):
    stamper.stamp(make_evaluation(name="cpu"))
    stamper.stamp(make_evaluation(name="mem"))
    names = stamper.all_names()
    assert "cpu" in names
    assert "mem" in names


def test_to_dict_has_expected_keys(stamper):
    ev = make_evaluation(name="pipeline_lag", value=42.0, status=MetricStatus.WARNING)
    stamped = stamper.stamp(ev)
    d = stamped.to_dict()
    for key in ("metric_name", "status", "value", "stamped_at", "stamp_id", "sequence"):
        assert key in d
    assert d["metric_name"] == "pipeline_lag"
    assert d["value"] == 42.0
    assert d["sequence"] == 1
