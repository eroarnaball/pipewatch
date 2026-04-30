"""Tests for pipewatch.splitter."""
import pytest
from unittest.mock import MagicMock
from pipewatch.splitter import SplitRule, AlertSplitter, SplitResult
from pipewatch.alerts import AlertMessage, AlertChannel


def make_message(metric_name="pipeline.latency", status="critical", value=9.5) -> AlertMessage:
    return AlertMessage(metric_name=metric_name, status=status, value=value, message="test")


def make_mock_channel() -> AlertChannel:
    ch = MagicMock(spec=AlertChannel)
    return ch


def make_splitter() -> AlertSplitter:
    return AlertSplitter()


def test_add_rule_returns_rule():
    s = make_splitter()
    ch = make_mock_channel()
    rule = s.add_rule(SplitRule(name="r1", channels=[ch]))
    assert rule.name == "r1"


def test_rules_list_grows():
    s = make_splitter()
    ch = make_mock_channel()
    s.add_rule(SplitRule(name="r1", channels=[ch]))
    s.add_rule(SplitRule(name="r2", channels=[ch]))
    assert len(s.rules) == 2


def test_rule_with_no_filters_matches_any():
    ch = make_mock_channel()
    rule = SplitRule(name="all", channels=[ch])
    assert rule.matches(make_message(metric_name="anything", status="ok"))


def test_rule_with_prefix_matches_correctly():
    ch = make_mock_channel()
    rule = SplitRule(name="db", channels=[ch], metric_prefix="db.")
    assert rule.matches(make_message(metric_name="db.latency"))
    assert not rule.matches(make_message(metric_name="cache.latency"))


def test_rule_with_min_severity_filters_ok():
    ch = make_mock_channel()
    rule = SplitRule(name="warn+", channels=[ch], min_severity="warning")
    assert not rule.matches(make_message(status="ok"))
    assert rule.matches(make_message(status="warning"))
    assert rule.matches(make_message(status="critical"))


def test_rule_with_min_severity_critical_only():
    ch = make_mock_channel()
    rule = SplitRule(name="crit", channels=[ch], min_severity="critical")
    assert not rule.matches(make_message(status="warning"))
    assert rule.matches(make_message(status="critical"))


def test_dispatch_calls_matching_channel():
    s = make_splitter()
    ch = make_mock_channel()
    s.add_rule(SplitRule(name="all", channels=[ch]))
    msg = make_message()
    result = s.dispatch(msg)
    ch.send.assert_called_once_with(msg)
    assert "all" in result.dispatched_to


def test_dispatch_skips_non_matching_rule():
    s = make_splitter()
    ch = make_mock_channel()
    s.add_rule(SplitRule(name="db-only", channels=[ch], metric_prefix="db."))
    msg = make_message(metric_name="cache.hit")
    result = s.dispatch(msg)
    ch.send.assert_not_called()
    assert "db-only" in result.skipped_rules


def test_dispatch_result_to_dict_has_expected_keys():
    s = make_splitter()
    ch = make_mock_channel()
    s.add_rule(SplitRule(name="r1", channels=[ch]))
    msg = make_message()
    result = s.dispatch(msg)
    d = result.to_dict()
    assert "metric_name" in d
    assert "status" in d
    assert "dispatched_to" in d
    assert "skipped_rules" in d


def test_split_rule_to_dict_has_expected_keys():
    ch = make_mock_channel()
    rule = SplitRule(name="test", channels=[ch, ch], metric_prefix="svc.", min_severity="warning")
    d = rule.to_dict()
    assert d["name"] == "test"
    assert d["metric_prefix"] == "svc."
    assert d["min_severity"] == "warning"
    assert d["channel_count"] == 2
