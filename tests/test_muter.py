"""Tests for pipewatch.muter."""

from datetime import datetime, timedelta, timezone

import pytest

from pipewatch.muter import AlertMuter, MuteEntry


def _now() -> datetime:
    return datetime.now(timezone.utc)


def make_muter() -> AlertMuter:
    return AlertMuter()


def test_mute_creates_entry():
    m = make_muter()
    entry = m.mute("pipeline.errors", "maintenance")
    assert isinstance(entry, MuteEntry)
    assert entry.metric_pattern == "pipeline.errors"
    assert entry.reason == "maintenance"
    assert entry.expires_at is None


def test_mute_with_duration_sets_expiry():
    m = make_muter()
    entry = m.mute("pipeline.errors", "deploy", duration_seconds=300)
    assert entry.expires_at is not None
    assert entry.expires_at > entry.muted_at


def test_is_muted_returns_true_for_exact_match():
    m = make_muter()
    m.mute("pipeline.errors", "test")
    assert m.is_muted("pipeline.errors") is True


def test_is_muted_returns_false_for_unregistered():
    m = make_muter()
    assert m.is_muted("pipeline.errors") is False


def test_is_muted_uses_glob_pattern():
    m = make_muter()
    m.mute("pipeline.*", "wildcard test")
    assert m.is_muted("pipeline.errors") is True
    assert m.is_muted("pipeline.latency") is True
    assert m.is_muted("other.metric") is False


def test_is_muted_returns_false_after_expiry():
    m = make_muter()
    past = _now() - timedelta(seconds=10)
    m.mute("pipeline.errors", "expired", duration_seconds=1, at=past)
    assert m.is_muted("pipeline.errors") is False


def test_unmute_removes_entry():
    m = make_muter()
    m.mute("pipeline.errors", "test")
    removed = m.unmute("pipeline.errors")
    assert removed is True
    assert m.is_muted("pipeline.errors") is False


def test_unmute_returns_false_for_unknown():
    m = make_muter()
    assert m.unmute("nonexistent") is False


def test_active_entries_excludes_expired():
    m = make_muter()
    past = _now() - timedelta(seconds=60)
    m.mute("expired.metric", "old", duration_seconds=1, at=past)
    m.mute("active.metric", "current")
    active = m.active_entries()
    assert len(active) == 1
    assert active[0].metric_pattern == "active.metric"


def test_purge_expired_removes_expired_entries():
    m = make_muter()
    past = _now() - timedelta(seconds=60)
    m.mute("expired.metric", "old", duration_seconds=1, at=past)
    m.mute("active.metric", "current")
    removed = m.purge_expired()
    assert removed == 1
    assert len(m.active_entries()) == 1


def test_to_dict_has_expected_keys():
    m = make_muter()
    entry = m.mute("pipeline.*", "testing", duration_seconds=60)
    d = entry.to_dict()
    assert "metric_pattern" in d
    assert "reason" in d
    assert "muted_at" in d
    assert "expires_at" in d
    assert "active" in d
    assert d["active"] is True
