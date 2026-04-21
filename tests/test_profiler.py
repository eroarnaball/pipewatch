"""Tests for pipewatch.profiler."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from pipewatch.profiler import MetricProfiler, ProfileEntry, ProfileSummary
from pipewatch.profiler_cli import profiler


def make_profiler(*records: tuple) -> MetricProfiler:
    """records is a sequence of (metric_name, duration_ms) tuples."""
    p = MetricProfiler()
    for name, dur in records:
        p.record(name, dur)
    return p


def test_record_returns_entry():
    p = MetricProfiler()
    entry = p.record("latency", 42.5)
    assert isinstance(entry, ProfileEntry)
    assert entry.metric_name == "latency"
    assert entry.duration_ms == 42.5


def test_entries_for_filters_by_name():
    p = make_profiler(("latency", 10.0), ("error_rate", 5.0), ("latency", 20.0))
    entries = p.entries_for("latency")
    assert len(entries) == 2
    assert all(e.metric_name == "latency" for e in entries)


def test_entries_for_unknown_returns_empty():
    p = make_profiler(("latency", 10.0))
    assert p.entries_for("nonexistent") == []


def test_summarize_returns_none_for_unknown():
    p = MetricProfiler()
    assert p.summarize("missing") is None


def test_summarize_computes_correct_stats():
    p = make_profiler(("row_count", 10.0), ("row_count", 20.0), ("row_count", 30.0))
    s = p.summarize("row_count")
    assert isinstance(s, ProfileSummary)
    assert s.count == 3
    assert s.min_ms == 10.0
    assert s.max_ms == 30.0
    assert abs(s.avg_ms - 20.0) < 1e-6


def test_all_summaries_covers_all_metrics():
    p = make_profiler(("a", 1.0), ("b", 2.0), ("a", 3.0))
    summaries = p.all_summaries()
    names = {s.metric_name for s in summaries}
    assert names == {"a", "b"}


def test_max_entries_enforced():
    p = MetricProfiler(max_entries=3)
    for i in range(5):
        p.record("m", float(i))
    assert len(p.entries_for("m")) == 3


def test_clear_specific_metric():
    p = make_profiler(("a", 1.0), ("b", 2.0))
    p.clear("a")
    assert p.entries_for("a") == []
    assert len(p.entries_for("b")) == 1


def test_clear_all():
    p = make_profiler(("a", 1.0), ("b", 2.0))
    p.clear()
    assert p.all_summaries() == []


def test_cli_list_table_output():
    runner = CliRunner()
    result = runner.invoke(profiler, ["list"])
    assert result.exit_code == 0
    assert "METRIC" in result.output
    assert "AVG ms" in result.output


def test_cli_list_json_output():
    runner = CliRunner()
    result = runner.invoke(profiler, ["list", "--format", "json"])
    assert result.exit_code == 0
    import json
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert "metric_name" in data[0]
    assert "avg_ms" in data[0]


def test_cli_detail_known_metric():
    runner = CliRunner()
    result = runner.invoke(profiler, ["detail", "latency"])
    assert result.exit_code == 0
    assert "latency" in result.output


def test_cli_detail_unknown_metric_exits_nonzero():
    runner = CliRunner()
    result = runner.invoke(profiler, ["detail", "nonexistent_metric_xyz"])
    assert result.exit_code != 0
