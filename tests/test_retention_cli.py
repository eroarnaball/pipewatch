"""Tests for pipewatch.retention_cli."""

from __future__ import annotations

import json

from click.testing import CliRunner

from pipewatch.retention_cli import retention


def test_run_retention_default_output():
    runner = CliRunner()
    result = runner.invoke(retention, ["run"])
    assert result.exit_code == 0
    assert "demo" in result.output


def test_run_retention_json_output():
    runner = CliRunner()
    result = runner.invoke(retention, ["run", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 1
    assert "metric_name" in data[0]
    assert "removed" in data[0]
    assert "remaining" in data[0]


def test_run_retention_short_ttl_removes_more():
    runner = CliRunner()
    result = runner.invoke(retention, ["run", "--ttl", "50", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    # entries at 3600 s and 90000 s should be pruned (both > 50 s)
    assert data[0]["removed"] >= 2


def test_show_policy_contains_ttl():
    runner = CliRunner()
    result = runner.invoke(retention, ["policy", "--ttl", "7200"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["default_ttl_seconds"] == 7200


def test_show_policy_default_ttl():
    runner = CliRunner()
    result = runner.invoke(retention, ["policy"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["default_ttl_seconds"] == 86400
