"""Tests for pipewatch.suppressor."""

from datetime import datetime, timedelta
import pytest
from pipewatch.suppressor import SuppressionRule, AlertSuppressor


UTC_NOW = datetime(2024, 6, 1, 12, 0, 0)
PAST = UTC_NOW - timedelta(hours=2)
FUTURE = UTC_NOW + timedelta(hours=2)


def make_rule(metric="latency", start=None, end=None, reason="maintenance"):
    return SuppressionRule(
        metric_name=metric,
        reason=reason,
        start=start or PAST,
        end=end,
    )


def test_rule_active_within_window():
    rule = make_rule(start=PAST, end=FUTURE)
    assert rule.is_active(at=UTC_NOW) is True


def test_rule_inactive_before_start():
    rule = make_rule(start=FUTURE, end=None)
    assert rule.is_active(at=UTC_NOW) is False


def test_rule_inactive_after_end():
    rule = make_rule(start=PAST, end=PAST + timedelta(minutes=1))
    assert rule.is_active(at=UTC_NOW) is False


def test_indefinite_rule_stays_active():
    rule = make_rule(start=PAST, end=None)
    assert rule.is_active(at=UTC_NOW) is True


def test_suppressor_detects_suppressed_metric():
    s = AlertSuppressor()
    s.add_rule(make_rule(metric="latency", start=PAST, end=FUTURE))
    assert s.is_suppressed("latency", at=UTC_NOW) is True


def test_suppressor_not_suppressed_for_other_metric():
    s = AlertSuppressor()
    s.add_rule(make_rule(metric="latency", start=PAST, end=FUTURE))
    assert s.is_suppressed("error_rate", at=UTC_NOW) is False


def test_suppressor_remove_rules():
    s = AlertSuppressor()
    s.add_rule(make_rule(metric="latency"))
    removed = s.remove_rules_for("latency")
    assert removed == 1
    assert s.is_suppressed("latency", at=UTC_NOW) is False


def test_active_rules_filters_expired():
    s = AlertSuppressor()
    s.add_rule(make_rule(metric="a", start=PAST, end=FUTURE))
    s.add_rule(make_rule(metric="b", start=PAST, end=PAST + timedelta(seconds=1)))
    active = s.active_rules(at=UTC_NOW)
    assert len(active) == 1
    assert active[0].metric_name == "a"


def test_to_dict_has_expected_keys():
    rule = make_rule(start=PAST, end=FUTURE)
    d = rule.to_dict()
    assert set(d.keys()) == {"metric_name", "reason", "start", "end", "active"}
