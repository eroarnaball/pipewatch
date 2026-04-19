"""Tests for NotificationThrottle in pipewatch.notifier."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from pipewatch.metrics import MetricStatus
from pipewatch.notifier import NotificationThrottle


FAKE_NOW = datetime(2024, 1, 1, 12, 0, 0)


def make_throttle(**kwargs):
    return NotificationThrottle(cooldown_seconds=300, repeat_interval_seconds=3600, **kwargs)


def test_first_warning_triggers_notification():
    t = make_throttle()
    with patch("pipewatch.notifier.datetime") as mock_dt:
        mock_dt.utcnow.return_value = FAKE_NOW
        assert t.should_notify("pipeline.lag", MetricStatus.WARNING) is True


def test_ok_status_does_not_notify_and_clears_state():
    t = make_throttle()
    with patch("pipewatch.notifier.datetime") as mock_dt:
        mock_dt.utcnow.return_value = FAKE_NOW
        t.should_notify("pipeline.lag", MetricStatus.WARNING)
        result = t.should_notify("pipeline.lag", MetricStatus.OK)
    assert result is False
    assert t.state_for("pipeline.lag") is None


def test_duplicate_within_cooldown_suppressed():
    t = make_throttle()
    with patch("pipewatch.notifier.datetime") as mock_dt:
        mock_dt.utcnow.return_value = FAKE_NOW
        t.should_notify("pipeline.lag", MetricStatus.WARNING)
        mock_dt.utcnow.return_value = FAKE_NOW + timedelta(seconds=60)
        result = t.should_notify("pipeline.lag", MetricStatus.WARNING)
    assert result is False


def test_escalation_to_critical_triggers_notification():
    t = make_throttle()
    with patch("pipewatch.notifier.datetime") as mock_dt:
        mock_dt.utcnow.return_value = FAKE_NOW
        t.should_notify("pipeline.lag", MetricStatus.WARNING)
        mock_dt.utcnow.return_value = FAKE_NOW + timedelta(seconds=120)
        result = t.should_notify("pipeline.lag", MetricStatus.CRITICAL)
    assert result is True


def test_repeat_after_repeat_interval():
    t = make_throttle()
    with patch("pipewatch.notifier.datetime") as mock_dt:
        mock_dt.utcnow.return_value = FAKE_NOW
        t.should_notify("pipeline.lag", MetricStatus.CRITICAL)
        mock_dt.utcnow.return_value = FAKE_NOW + timedelta(seconds=3601)
        result = t.should_notify("pipeline.lag", MetricStatus.CRITICAL)
    assert result is True


def test_reset_clears_specific_metric():
    t = make_throttle()
    with patch("pipewatch.notifier.datetime") as mock_dt:
        mock_dt.utcnow.return_value = FAKE_NOW
        t.should_notify("a", MetricStatus.WARNING)
        t.should_notify("b", MetricStatus.CRITICAL)
    t.reset("a")
    assert t.state_for("a") is None
    assert t.state_for("b") is not None


def test_reset_all_clears_all_state():
    t = make_throttle()
    with patch("pipewatch.notifier.datetime") as mock_dt:
        mock_dt.utcnow.return_value = FAKE_NOW
        t.should_notify("a", MetricStatus.WARNING)
        t.should_notify("b", MetricStatus.CRITICAL)
    t.reset()
    assert t.state_for("a") is None
    assert t.state_for("b") is None
