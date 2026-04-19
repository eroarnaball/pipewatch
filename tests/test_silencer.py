"""Tests for pipewatch.silencer."""

from datetime import datetime, timedelta
import pytest
from pipewatch.silencer import MetricSilencer, SilenceEntry


def make_silencer() -> MetricSilencer:
    return MetricSilencer()


def test_silence_creates_entry():
    s = make_silencer()
    entry = s.silence("cpu_usage", reason="maintenance")
    assert isinstance(entry, SilenceEntry)
    assert entry.metric_name == "cpu_usage"
    assert entry.reason == "maintenance"
    assert entry.expires_at is None


def test_is_silenced_returns_true_for_active():
    s = make_silencer()
    s.silence("cpu_usage", reason="maintenance")
    assert s.is_silenced("cpu_usage") is True


def test_is_silenced_returns_false_for_unknown():
    s = make_silencer()
    assert s.is_silenced("unknown_metric") is False


def test_unsilence_removes_entry():
    s = make_silencer()
    s.silence("cpu_usage", reason="maintenance")
    result = s.unsilence("cpu_usage")
    assert result is True
    assert s.is_silenced("cpu_usage") is False


def test_unsilence_returns_false_when_not_present():
    s = make_silencer()
    assert s.unsilence("nonexistent") is False


def test_expired_silence_not_active():
    s = make_silencer()
    now = datetime.utcnow()
    past = now - timedelta(hours=1)
    s.silence("cpu_usage", reason="old", expires_at=past, now=now - timedelta(hours=2))
    assert s.is_silenced("cpu_usage", now=now) is False


def test_future_expiry_still_active():
    s = make_silencer()
    now = datetime.utcnow()
    future = now + timedelta(hours=1)
    s.silence("cpu_usage", reason="planned", expires_at=future, now=now)
    assert s.is_silenced("cpu_usage", now=now) is True


def test_active_silences_lists_only_active():
    s = make_silencer()
    now = datetime.utcnow()
    s.silence("m1", reason="a", expires_at=now + timedelta(hours=1), now=now)
    s.silence("m2", reason="b", expires_at=now - timedelta(hours=1), now=now - timedelta(hours=2))
    active = s.active_silences(now=now)
    names = [e.metric_name for e in active]
    assert "m1" in names
    assert "m2" not in names


def test_purge_expired_removes_stale_entries():
    s = make_silencer()
    now = datetime.utcnow()
    s.silence("m1", reason="a", expires_at=now - timedelta(minutes=5), now=now - timedelta(hours=1))
    s.silence("m2", reason="b")
    removed = s.purge_expired(now=now)
    assert removed == 1
    assert s.is_silenced("m1", now=now) is False
    assert s.is_silenced("m2", now=now) is True


def test_to_dict_keys():
    s = make_silencer()
    entry = s.silence("latency", reason="deploy")
    d = entry.to_dict()
    assert set(d.keys()) == {"metric_name", "reason", "silenced_at", "expires_at", "active"}
