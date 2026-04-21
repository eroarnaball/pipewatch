"""Tests for pipewatch.cooldown."""

from datetime import datetime, timedelta

import pytest

from pipewatch.cooldown import AlertCooldown, CooldownEntry


def make_cooldown(default_seconds: float = 300.0) -> AlertCooldown:
    return AlertCooldown(default_seconds=default_seconds)


def test_trigger_creates_entry():
    cd = make_cooldown()
    now = datetime.utcnow()
    entry = cd.trigger("my_metric", now=now)
    assert isinstance(entry, CooldownEntry)
    assert entry.metric_name == "my_metric"
    assert entry.triggered_at == now


def test_is_cooling_returns_true_within_window():
    cd = make_cooldown(default_seconds=60)
    now = datetime.utcnow()
    cd.trigger("my_metric", now=now)
    assert cd.is_cooling("my_metric", now=now + timedelta(seconds=30))


def test_is_cooling_returns_false_after_expiry():
    cd = make_cooldown(default_seconds=60)
    now = datetime.utcnow()
    cd.trigger("my_metric", now=now)
    assert not cd.is_cooling("my_metric", now=now + timedelta(seconds=61))


def test_is_cooling_returns_false_for_unknown_metric():
    cd = make_cooldown()
    assert not cd.is_cooling("nonexistent")


def test_override_duration_is_respected():
    cd = make_cooldown(default_seconds=300)
    cd.set_override("fast_metric", 10)
    now = datetime.utcnow()
    cd.trigger("fast_metric", now=now)
    assert cd.is_cooling("fast_metric", now=now + timedelta(seconds=5))
    assert not cd.is_cooling("fast_metric", now=now + timedelta(seconds=11))


def test_clear_removes_entry():
    cd = make_cooldown()
    cd.trigger("my_metric")
    cd.clear("my_metric")
    assert not cd.is_cooling("my_metric")
    assert "my_metric" not in cd.all_entries()


def test_clear_nonexistent_is_safe():
    cd = make_cooldown()
    cd.clear("ghost_metric")  # should not raise


def test_to_dict_contains_expected_keys():
    cd = make_cooldown(default_seconds=120)
    now = datetime.utcnow()
    entry = cd.trigger("check_metric", now=now)
    d = entry.to_dict()
    assert "metric_name" in d
    assert "triggered_at" in d
    assert "expires_at" in d
    assert "duration_seconds" in d
    assert "active" in d
    assert d["duration_seconds"] == 120.0


def test_all_entries_returns_all_tracked():
    cd = make_cooldown()
    cd.trigger("a")
    cd.trigger("b")
    cd.trigger("c")
    assert set(cd.all_entries().keys()) == {"a", "b", "c"}
