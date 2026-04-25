"""Tests for pipewatch.acknowledger."""

from datetime import datetime, timedelta

import pytest

from pipewatch.acknowledger import AcknowledgementEntry, MetricAcknowledger


def make_acknowledger() -> MetricAcknowledger:
    return MetricAcknowledger()


def test_acknowledge_creates_entry():
    ack = make_acknowledger()
    entry = ack.acknowledge("cpu_usage", "alice", "Known spike during deploy")
    assert entry.metric_name == "cpu_usage"
    assert entry.acknowledged_by == "alice"
    assert entry.reason == "Known spike during deploy"
    assert entry.expires_at is None


def test_is_acknowledged_returns_true_for_active():
    ack = make_acknowledger()
    ack.acknowledge("cpu_usage", "alice", "reason")
    assert ack.is_acknowledged("cpu_usage") is True


def test_is_acknowledged_returns_false_for_unknown():
    ack = make_acknowledger()
    assert ack.is_acknowledged("missing_metric") is False


def test_is_acknowledged_returns_false_after_expiry():
    ack = make_acknowledger()
    past = datetime.utcnow() - timedelta(seconds=1)
    ack.acknowledge("cpu_usage", "alice", "reason", expires_at=past)
    now = datetime.utcnow()
    assert ack.is_acknowledged("cpu_usage", now=now) is False


def test_is_acknowledged_returns_true_before_expiry():
    ack = make_acknowledger()
    future = datetime.utcnow() + timedelta(hours=1)
    ack.acknowledge("cpu_usage", "alice", "reason", expires_at=future)
    assert ack.is_acknowledged("cpu_usage") is True


def test_unacknowledge_removes_entry():
    ack = make_acknowledger()
    ack.acknowledge("cpu_usage", "alice", "reason")
    result = ack.unacknowledge("cpu_usage")
    assert result is True
    assert ack.is_acknowledged("cpu_usage") is False


def test_unacknowledge_returns_false_for_unknown():
    ack = make_acknowledger()
    result = ack.unacknowledge("nonexistent")
    assert result is False


def test_get_returns_entry():
    ack = make_acknowledger()
    ack.acknowledge("latency", "bob", "investigating")
    entry = ack.get("latency")
    assert entry is not None
    assert entry.acknowledged_by == "bob"


def test_get_returns_none_for_unknown():
    ack = make_acknowledger()
    assert ack.get("unknown") is None


def test_all_active_excludes_expired():
    ack = make_acknowledger()
    past = datetime.utcnow() - timedelta(seconds=10)
    future = datetime.utcnow() + timedelta(hours=1)
    ack.acknowledge("metric_a", "alice", "reason", expires_at=past)
    ack.acknowledge("metric_b", "bob", "reason", expires_at=future)
    active = ack.all_active()
    names = [e.metric_name for e in active]
    assert "metric_b" in names
    assert "metric_a" not in names


def test_entry_to_dict_has_expected_keys():
    ack = make_acknowledger()
    entry = ack.acknowledge("error_rate", "carol", "expected")
    d = entry.to_dict()
    assert "metric_name" in d
    assert "acknowledged_by" in d
    assert "reason" in d
    assert "acknowledged_at" in d
    assert "expires_at" in d
    assert "active" in d
