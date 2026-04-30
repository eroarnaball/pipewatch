"""Tests for pipewatch.ticker_cli."""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from pipewatch.ticker_cli import ticker


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_stats_table_contains_headers(runner):
    result = runner.invoke(ticker, ["stats"])
    assert result.exit_code == 0
    assert "Metric" in result.output
    assert "Ticks" in result.output
    assert "Avg(s)" in result.output


def test_stats_table_shows_metric_rows(runner):
    result = runner.invoke(ticker, ["stats"])
    assert result.exit_code == 0
    assert "orders.latency" in result.output
    assert "queue.depth" in result.output


def test_stats_json_output_is_valid(runner):
    result = runner.invoke(ticker, ["stats", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) >= 1


def test_stats_json_contains_expected_keys(runner):
    result = runner.invoke(ticker, ["stats", "--format", "json"])
    data = json.loads(result.output)
    entry = data[0]
    assert "metric_name" in entry
    assert "tick_count" in entry
    assert "avg_interval_seconds" in entry


def test_detail_known_metric(runner):
    result = runner.invoke(ticker, ["detail", "orders.latency"])
    assert result.exit_code == 0
    assert "orders.latency" in result.output


def test_detail_json_output(runner):
    result = runner.invoke(ticker, ["detail", "orders.latency", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert all("ticked_at" in e for e in data)


def test_detail_unknown_metric_exits_nonzero(runner):
    result = runner.invoke(ticker, ["detail", "nonexistent.metric"])
    assert result.exit_code != 0
