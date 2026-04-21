"""Tests for pipewatch.escalation."""

from datetime import datetime, timedelta

import pytest

from pipewatch.escalation import AlertEscalator, EscalationPolicy
from pipewatch.metrics import MetricStatus


def make_escalator(after: int = 3, window: int = 300) -> AlertEscalator:
    return AlertEscalator(policy=EscalationPolicy(escalate_after=after, escalate_window=window))


def test_ok_status_returns_ok_and_does_not_escalate():
    esc = make_escalator()
    result = esc.evaluate("m", MetricStatus.OK)
    assert result.effective_status == MetricStatus.OK
    assert not result.escalated
    assert result.consecutive_warnings == 0


def test_critical_status_passes_through_unchanged():
    esc = make_escalator()
    result = esc.evaluate("m", MetricStatus.CRITICAL)
    assert result.effective_status == MetricStatus.CRITICAL
    assert not result.escalated


def test_single_warning_is_not_escalated():
    esc = make_escalator(after=3)
    result = esc.evaluate("m", MetricStatus.WARNING)
    assert result.effective_status == MetricStatus.WARNING
    assert not result.escalated
    assert result.consecutive_warnings == 1


def test_warnings_below_threshold_not_escalated():
    esc = make_escalator(after=3)
    base = datetime.utcnow()
    for i in range(2):
        result = esc.evaluate("m", MetricStatus.WARNING, now=base + timedelta(seconds=i * 10))
    assert result.effective_status == MetricStatus.WARNING
    assert not result.escalated


def test_warnings_at_threshold_escalates():
    esc = make_escalator(after=3)
    base = datetime.utcnow()
    for i in range(3):
        result = esc.evaluate("m", MetricStatus.WARNING, now=base + timedelta(seconds=i * 10))
    assert result.effective_status == MetricStatus.CRITICAL
    assert result.escalated
    assert result.consecutive_warnings == 3


def test_ok_resets_escalation_state():
    esc = make_escalator(after=2)
    base = datetime.utcnow()
    esc.evaluate("m", MetricStatus.WARNING, now=base)
    esc.evaluate("m", MetricStatus.WARNING, now=base + timedelta(seconds=10))
    esc.evaluate("m", MetricStatus.OK, now=base + timedelta(seconds=20))
    result = esc.evaluate("m", MetricStatus.WARNING, now=base + timedelta(seconds=30))
    assert result.effective_status == MetricStatus.WARNING
    assert not result.escalated
    assert result.consecutive_warnings == 1


def test_warnings_outside_window_reset_count():
    esc = make_escalator(after=3, window=60)
    base = datetime.utcnow()
    esc.evaluate("m", MetricStatus.WARNING, now=base)
    esc.evaluate("m", MetricStatus.WARNING, now=base + timedelta(seconds=30))
    # beyond the 60-second window
    result = esc.evaluate("m", MetricStatus.WARNING, now=base + timedelta(seconds=120))
    assert result.consecutive_warnings == 1
    assert not result.escalated


def test_result_to_dict_has_expected_keys():
    esc = make_escalator()
    result = esc.evaluate("latency", MetricStatus.WARNING)
    d = result.to_dict()
    assert "metric_name" in d
    assert "original_status" in d
    assert "effective_status" in d
    assert "escalated" in d
    assert "consecutive_warnings" in d


def test_manual_reset_clears_state():
    esc = make_escalator(after=2)
    base = datetime.utcnow()
    esc.evaluate("m", MetricStatus.WARNING, now=base)
    esc.evaluate("m", MetricStatus.WARNING, now=base + timedelta(seconds=5))
    esc.reset("m")
    result = esc.evaluate("m", MetricStatus.WARNING, now=base + timedelta(seconds=10))
    assert result.consecutive_warnings == 1
    assert not result.escalated
