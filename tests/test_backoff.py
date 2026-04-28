"""Tests for pipewatch.backoff."""
import time
from unittest.mock import patch

import pytest

from pipewatch.backoff import AlertBackoff, BackoffResult, BackoffState


def make_backoff(**kwargs) -> AlertBackoff:
    return AlertBackoff(base_delay=10.0, multiplier=2.0, max_delay=120.0, **kwargs)


def test_first_check_is_allowed():
    ab = make_backoff()
    result = ab.check("my.metric")
    assert isinstance(result, BackoffResult)
    assert result.allowed is True
    assert result.attempt == 0
    assert result.wait_seconds == 0.0


def test_second_check_within_delay_is_blocked():
    ab = make_backoff()
    ab.check("my.metric")  # first: allowed, schedules next in 10s
    result = ab.check("my.metric")  # second: blocked
    assert result.allowed is False
    assert result.wait_seconds > 0


def test_check_after_delay_is_allowed():
    ab = make_backoff(base_delay=1.0)
    ab.check("my.metric")
    with patch("pipewatch.backoff.time.time", return_value=time.time() + 5.0):
        result = ab.check("my.metric")
    assert result.allowed is True


def test_attempt_increments_on_each_allowed_check():
    ab = make_backoff(base_delay=0.0)
    r1 = ab.check("x")
    r2 = ab.check("x")
    assert r1.attempt == 0
    assert r2.attempt == 1


def test_delay_doubles_with_multiplier():
    ab = AlertBackoff(base_delay=5.0, multiplier=2.0, max_delay=9999.0)
    # attempt 0 -> delay 5s, attempt 1 -> 10s, attempt 2 -> 20s
    assert ab._delay_for(0) == pytest.approx(5.0)
    assert ab._delay_for(1) == pytest.approx(10.0)
    assert ab._delay_for(2) == pytest.approx(20.0)


def test_delay_capped_at_max_delay():
    ab = AlertBackoff(base_delay=5.0, multiplier=2.0, max_delay=15.0)
    assert ab._delay_for(10) == pytest.approx(15.0)


def test_reset_clears_state():
    ab = make_backoff()
    ab.check("my.metric")
    assert ab.state_for("my.metric") is not None
    ab.reset("my.metric")
    assert ab.state_for("my.metric") is None


def test_reset_unknown_metric_is_noop():
    ab = make_backoff()
    ab.reset("nonexistent")  # should not raise


def test_state_for_returns_none_for_unknown():
    ab = make_backoff()
    assert ab.state_for("unknown") is None


def test_all_states_returns_all_tracked_metrics():
    ab = make_backoff()
    ab.check("metric.a")
    ab.check("metric.b")
    states = ab.all_states()
    assert "metric.a" in states
    assert "metric.b" in states
    assert len(states) == 2


def test_backoff_state_to_dict_has_expected_keys():
    state = BackoffState(metric_name="test", attempt=3, next_allowed_at=12345.0)
    d = state.to_dict()
    assert "metric_name" in d
    assert "attempt" in d
    assert "next_allowed_at" in d


def test_backoff_result_to_dict_has_expected_keys():
    result = BackoffResult(metric_name="x", allowed=True, attempt=1, wait_seconds=0.0)
    d = result.to_dict()
    assert "metric_name" in d
    assert "allowed" in d
    assert "attempt" in d
    assert "wait_seconds" in d


def test_independent_state_per_metric():
    ab = make_backoff(base_delay=0.0)
    ab.check("a")
    ab.check("a")
    ab.check("b")
    assert ab.state_for("a").attempt == 2
    assert ab.state_for("b").attempt == 1
