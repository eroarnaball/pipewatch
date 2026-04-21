"""Tests for the circuit breaker module."""

import time
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from pipewatch.circuit_breaker import CircuitBreaker, CircuitBreakerRegistry, CircuitState


def make_breaker(threshold: int = 3, recovery: int = 60) -> CircuitBreaker:
    return CircuitBreaker(channel_name="test", failure_threshold=threshold, recovery_timeout=recovery)


def test_initial_state_is_closed():
    cb = make_breaker()
    assert cb.state == CircuitState.CLOSED


def test_allow_request_when_closed():
    cb = make_breaker()
    assert cb.allow_request() is True


def test_single_failure_does_not_open():
    cb = make_breaker(threshold=3)
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED


def test_failures_at_threshold_open_circuit():
    cb = make_breaker(threshold=3)
    cb.record_failure()
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.is_open() is True
    assert cb.allow_request() is False


def test_success_resets_failures_and_closes():
    cb = make_breaker(threshold=2)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    cb.record_success()
    assert cb.state == CircuitState.CLOSED
    assert cb._failures == 0


def test_half_open_after_recovery_timeout():
    cb = make_breaker(threshold=1, recovery=30)
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

    future = datetime.utcnow() - timedelta(seconds=31)
    cb._opened_at = future
    assert cb.state == CircuitState.HALF_OPEN
    assert cb.allow_request() is True


def test_reset_clears_state():
    cb = make_breaker(threshold=1)
    cb.record_failure()
    assert cb.is_open()
    cb.reset()
    assert cb.state == CircuitState.CLOSED
    assert cb._failures == 0
    assert cb._opened_at is None


def test_to_dict_keys():
    cb = make_breaker()
    cb.record_failure()
    d = cb.to_dict()
    assert "channel" in d
    assert "state" in d
    assert "failures" in d
    assert "failure_threshold" in d
    assert "recovery_timeout" in d
    assert "opened_at" in d


def test_registry_creates_breaker_on_first_get():
    registry = CircuitBreakerRegistry()
    cb = registry.get("slack")
    assert cb.channel_name == "slack"
    assert cb.state == CircuitState.CLOSED


def test_registry_returns_same_instance():
    registry = CircuitBreakerRegistry()
    cb1 = registry.get("email")
    cb2 = registry.get("email")
    assert cb1 is cb2


def test_registry_all_states_returns_list():
    registry = CircuitBreakerRegistry()
    registry.get("a")
    registry.get("b")
    states = registry.all_states()
    assert len(states) == 2
    channels = {s["channel"] for s in states}
    assert channels == {"a", "b"}
