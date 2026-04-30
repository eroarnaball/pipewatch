"""Tests for pipewatch.ticker."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest

from pipewatch.ticker import MetricTicker, TickEntry, TickStats


def make_ticker(max_entries: int = 200) -> MetricTicker:
    return MetricTicker(max_entries=max_entries)


def _ts(offset_seconds: float = 0.0) -> datetime:
    base = datetime(2024, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
    return base + timedelta(seconds=offset_seconds)


def test_first_tick_has_no_interval():
    t = make_ticker()
    entry = t.tick("cpu", at=_ts(0))
    assert isinstance(entry, TickEntry)
    assert entry.interval_seconds is None


def test_second_tick_has_correct_interval():
    t = make_ticker()
    t.tick("cpu", at=_ts(0))
    entry = t.tick("cpu", at=_ts(30))
    assert entry.interval_seconds == pytest.approx(30.0)


def test_multiple_ticks_accumulate_entries():
    t = make_ticker()
    for i in range(5):
        t.tick("cpu", at=_ts(i * 10))
    entries = t.entries_for("cpu")
    assert len(entries) == 5


def test_max_entries_enforced():
    t = make_ticker(max_entries=3)
    for i in range(6):
        t.tick("cpu", at=_ts(i * 10))
    entries = t.entries_for("cpu")
    assert len(entries) == 3


def test_stats_returns_none_for_unknown_metric():
    t = make_ticker()
    assert t.stats("unknown") is None


def test_stats_tick_count_correct():
    t = make_ticker()
    for i in range(4):
        t.tick("latency", at=_ts(i * 20))
    stats = t.stats("latency")
    assert stats is not None
    assert stats.tick_count == 4


def test_stats_avg_interval():
    t = make_ticker()
    t.tick("latency", at=_ts(0))
    t.tick("latency", at=_ts(10))
    t.tick("latency", at=_ts(30))
    stats = t.stats("latency")
    assert stats is not None
    # intervals: 10, 20 -> avg = 15
    assert stats.avg_interval_seconds == pytest.approx(15.0)


def test_stats_min_max_interval():
    t = make_ticker()
    t.tick("latency", at=_ts(0))
    t.tick("latency", at=_ts(5))
    t.tick("latency", at=_ts(25))
    stats = t.stats("latency")
    assert stats is not None
    assert stats.min_interval_seconds == pytest.approx(5.0)
    assert stats.max_interval_seconds == pytest.approx(20.0)


def test_all_stats_returns_entry_per_metric():
    t = make_ticker()
    t.tick("a", at=_ts(0))
    t.tick("b", at=_ts(0))
    t.tick("c", at=_ts(0))
    all_s = t.all_stats()
    names = {s.metric_name for s in all_s}
    assert names == {"a", "b", "c"}


def test_to_dict_has_expected_keys():
    t = make_ticker()
    t.tick("m", at=_ts(0))
    stats = t.stats("m")
    assert stats is not None
    d = stats.to_dict()
    assert "metric_name" in d
    assert "tick_count" in d
    assert "avg_interval_seconds" in d
    assert "last_ticked_at" in d


def test_entries_for_unknown_returns_empty():
    t = make_ticker()
    assert t.entries_for("ghost") == []


def test_independent_tracking_per_metric():
    t = make_ticker()
    t.tick("a", at=_ts(0))
    t.tick("a", at=_ts(10))
    t.tick("b", at=_ts(0))
    assert len(t.entries_for("a")) == 2
    assert len(t.entries_for("b")) == 1
