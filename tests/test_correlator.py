"""Tests for pipewatch.correlator."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from pipewatch.correlator import CorrelationResult, MetricCorrelator
from pipewatch.history import HistoryEntry, MetricHistory
from pipewatch.metrics import MetricStatus

NOW = datetime.now(timezone.utc).timestamp()


def make_history(statuses, base_time=NOW, interval=30):
    h = MetricHistory(max_entries=100)
    for i, st in enumerate(statuses):
        h.record(
            HistoryEntry(
                metric_name="m",
                status=st,
                value=float(i),
                timestamp=base_time - (len(statuses) - i) * interval,
            )
        )
    return h


def make_correlator(*pairs):
    c = MetricCorrelator()
    for name, history in pairs:
        c.register(name, history)
    return c


OK = MetricStatus.OK
WARN = MetricStatus.WARNING
CRIT = MetricStatus.CRITICAL


def test_correlate_returns_none_for_unknown_metric():
    c = MetricCorrelator()
    c.register("a", make_history([OK]))
    assert c.correlate("a", "missing") is None


def test_correlate_both_unknown_returns_none():
    c = MetricCorrelator()
    assert c.correlate("x", "y") is None


def test_both_always_ok_score_is_zero():
    c = make_correlator(
        ("a", make_history([OK, OK, OK])),
        ("b", make_history([OK, OK, OK])),
    )
    r = c.correlate("a", "b")
    assert r is not None
    assert r.score == 0.0
    assert r.co_occurrences == 0


def test_identical_bad_patterns_score_is_one():
    pattern = [WARN, CRIT, WARN]
    c = make_correlator(
        ("a", make_history(pattern, interval=10)),
        ("b", make_history(pattern, interval=10)),
    )
    r = c.correlate("a", "b", window_seconds=5.0)
    assert r is not None
    assert r.score == 1.0


def test_no_overlap_gives_zero_score():
    # a degrades at t=0, b degrades at t=1000 — well outside window
    base = NOW
    h_a = MetricHistory(max_entries=10)
    h_a.record(HistoryEntry("a", CRIT, 1.0, base))
    h_b = MetricHistory(max_entries=10)
    h_b.record(HistoryEntry("b", CRIT, 1.0, base + 1000))
    c = make_correlator(("a", h_a), ("b", h_b))
    r = c.correlate("a", "b", window_seconds=30.0)
    assert r is not None
    assert r.score == 0.0


def test_top_correlations_filters_by_min_score():
    pattern = [WARN, CRIT]
    c = make_correlator(
        ("a", make_history(pattern, interval=5)),
        ("b", make_history(pattern, interval=5)),
        ("c", make_history([OK, OK], interval=5)),
    )
    results = c.top_correlations(window_seconds=10.0, min_score=0.8)
    names = {(r.metric_a, r.metric_b) for r in results}
    assert ("a", "b") in names
    for r in results:
        assert r.score >= 0.8


def test_top_correlations_sorted_descending():
    pattern_high = [WARN, CRIT, WARN, CRIT]
    pattern_low = [WARN, OK, OK, OK]
    c = make_correlator(
        ("a", make_history(pattern_high, interval=5)),
        ("b", make_history(pattern_high, interval=5)),
        ("c", make_history(pattern_low, interval=5)),
    )
    results = c.top_correlations(window_seconds=10.0, min_score=0.0)
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_correlation_result_to_dict_keys():
    r = CorrelationResult("x", "y", co_occurrences=3, total_events=5)
    d = r.to_dict()
    assert set(d.keys()) == {"metric_a", "metric_b", "co_occurrences", "total_events", "score"}
    assert d["score"] == pytest.approx(0.6, rel=1e-3)
