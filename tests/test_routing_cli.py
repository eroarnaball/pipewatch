"""Tests for pipewatch.routing_cli."""

import json
from click.testing import CliRunner
from pipewatch.routing_cli import routing


def test_list_table_output_contains_headers():
    runner = CliRunner()
    result = runner.invoke(routing, ["list"])
    assert result.exit_code == 0
    assert "RULE" in result.output
    assert "METRICS" in result.output
    assert "STATUSES" in result.output


def test_list_table_shows_rule_names():
    runner = CliRunner()
    result = runner.invoke(routing, ["list"])
    assert result.exit_code == 0
    assert "critical-all" in result.output
    assert "warning-latency" in result.output
    assert "all-errors" in result.output


def test_list_json_output_is_valid():
    runner = CliRunner()
    result = runner.invoke(routing, ["list", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) > 0


def test_list_json_contains_expected_keys():
    runner = CliRunner()
    result = runner.invoke(routing, ["list", "--format", "json"])
    data = json.loads(result.output)
    for entry in data:
        assert "name" in entry
        assert "metric_names" in entry
        assert "statuses" in entry


def test_simulate_critical_routes_to_rule():
    runner = CliRunner()
    result = runner.invoke(routing, ["simulate", "any_metric", "critical"])
    assert result.exit_code == 0
    assert "critical-all" in result.output


def test_simulate_ok_status_no_match():
    runner = CliRunner()
    result = runner.invoke(routing, ["simulate", "some_metric", "ok"])
    assert result.exit_code == 0
    assert "No matching rules" in result.output


def test_simulate_warning_latency_matches_specific_rule():
    runner = CliRunner()
    result = runner.invoke(routing, ["simulate", "latency", "warning"])
    assert result.exit_code == 0
    assert "warning-latency" in result.output
