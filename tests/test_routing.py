"""Tests for pipewatch.routing."""

import pytest
from unittest.mock import MagicMock

from pipewatch.metrics import MetricStatus, PipelineMetric
from pipewatch.thresholds import MetricEvaluation
from pipewatch.alerts import AlertChannel, AlertMessage
from pipewatch.routing import AlertRouter, RoutingRule


def make_evaluation(name: str, status: MetricStatus, value: float = 1.0) -> MetricEvaluation:
    metric = PipelineMetric(name=name, value=value, unit="ms")
    return MetricEvaluation(metric=metric, status=status, message=f"{name} is {status.value}")


def make_mock_channel() -> AlertChannel:
    ch = MagicMock(spec=AlertChannel)
    return ch


def test_rule_matches_any_when_no_filters():
    ch = make_mock_channel()
    rule = RoutingRule(name="catch-all", channel=ch)
    ev = make_evaluation("latency", MetricStatus.WARNING)
    assert rule.matches(ev) is True


def test_rule_matches_specific_metric_name():
    ch = make_mock_channel()
    rule = RoutingRule(name="r", channel=ch, metric_names=["latency"])
    assert rule.matches(make_evaluation("latency", MetricStatus.CRITICAL)) is True
    assert rule.matches(make_evaluation("throughput", MetricStatus.CRITICAL)) is False


def test_rule_matches_specific_status():
    ch = make_mock_channel()
    rule = RoutingRule(name="r", channel=ch, statuses=[MetricStatus.CRITICAL])
    assert rule.matches(make_evaluation("any", MetricStatus.CRITICAL)) is True
    assert rule.matches(make_evaluation("any", MetricStatus.WARNING)) is False


def test_rule_matches_combined_filters():
    ch = make_mock_channel()
    rule = RoutingRule(
        name="r", channel=ch,
        metric_names=["error_rate"],
        statuses=[MetricStatus.WARNING, MetricStatus.CRITICAL],
    )
    assert rule.matches(make_evaluation("error_rate", MetricStatus.WARNING)) is True
    assert rule.matches(make_evaluation("error_rate", MetricStatus.OK)) is False
    assert rule.matches(make_evaluation("latency", MetricStatus.CRITICAL)) is False


def test_router_fires_matching_rules():
    ch1, ch2 = make_mock_channel(), make_mock_channel()
    router = AlertRouter()
    router.add_rule(RoutingRule("r1", ch1, statuses=[MetricStatus.CRITICAL]))
    router.add_rule(RoutingRule("r2", ch2, statuses=[MetricStatus.WARNING]))

    ev = make_evaluation("latency", MetricStatus.CRITICAL)
    fired = router.route(ev)
    assert fired == ["r1"]
    ch1.send.assert_called_once()
    ch2.send.assert_not_called()


def test_router_fires_multiple_matching_rules():
    ch1, ch2 = make_mock_channel(), make_mock_channel()
    router = AlertRouter()
    router.add_rule(RoutingRule("r1", ch1))
    router.add_rule(RoutingRule("r2", ch2))

    ev = make_evaluation("latency", MetricStatus.WARNING)
    fired = router.route(ev)
    assert set(fired) == {"r1", "r2"}


def test_router_remove_rule():
    ch = make_mock_channel()
    router = AlertRouter()
    router.add_rule(RoutingRule("r1", ch))
    removed = router.remove_rule("r1")
    assert removed is True
    assert router.rules() == []


def test_router_remove_nonexistent_rule_returns_false():
    router = AlertRouter()
    assert router.remove_rule("ghost") is False


def test_rule_to_dict_keys():
    ch = make_mock_channel()
    rule = RoutingRule(
        name="test", channel=ch,
        metric_names=["m1"],
        statuses=[MetricStatus.CRITICAL],
    )
    d = rule.to_dict()
    assert d["name"] == "test"
    assert d["metric_names"] == ["m1"]
    assert d["statuses"] == ["critical"]
