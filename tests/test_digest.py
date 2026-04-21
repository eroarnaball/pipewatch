"""Tests for pipewatch.digest module."""

import pytest
from datetime import datetime
from pipewatch.digest import DigestBuilder, DigestEntry
from pipewatch.score_history import ScoreEntry
from pipewatch.metrics import MetricStatus


def make_entries():
    ts = datetime(2024, 1, 1, 12, 0, 0)
    return [
        ScoreEntry(metric_name="a", score=1.0, status=MetricStatus.OK, timestamp=ts),
        ScoreEntry(metric_name="b", score=0.5, status=MetricStatus.WARNING, timestamp=ts),
        ScoreEntry(metric_name="c", score=0.0, status=MetricStatus.CRITICAL, timestamp=ts),
    ]


def test_build_returns_none_for_empty_entries():
    builder = DigestBuilder()
    result = builder.build([])
    assert result is None


def test_build_counts_statuses():
    builder = DigestBuilder()
    entries = make_entries()
    result = builder.build(entries)
    assert result.ok_count == 1
    assert result.warning_count == 1
    assert result.critical_count == 1


def test_build_calculates_avg_score():
    builder = DigestBuilder()
    entries = make_entries()
    result = builder.build(entries)
    expected = round((1.0 + 0.5 + 0.0) / 3, 3)
    assert result.avg_score == pytest.approx(expected)


def test_build_top_issues_excludes_ok():
    builder = DigestBuilder(max_issues=5)
    entries = make_entries()
    result = builder.build(entries)
    assert "a" not in result.top_issues
    assert "b" in result.top_issues or "c" in result.top_issues


def test_build_top_issues_respects_max():
    ts = datetime.utcnow()
    entries = [
        ScoreEntry(metric_name=f"m{i}", score=0.1 * i, status=MetricStatus.WARNING, timestamp=ts)
        for i in range(10)
    ]
    builder = DigestBuilder(max_issues=3)
    result = builder.build(entries)
    assert len(result.top_issues) <= 3


def test_build_uses_provided_timestamp():
    fixed = datetime(2024, 6, 15, 8, 0, 0)
    builder = DigestBuilder()
    entries = make_entries()
    result = builder.build(entries, timestamp=fixed)
    assert result.timestamp == fixed


def test_to_dict_has_expected_keys():
    builder = DigestBuilder()
    entries = make_entries()
    result = builder.build(entries)
    d = result.to_dict()
    assert "timestamp" in d
    assert "ok_count" in d
    assert "warning_count" in d
    assert "critical_count" in d
    assert "avg_score" in d
    assert "top_issues" in d
