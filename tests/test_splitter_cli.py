"""Tests for pipewatch.splitter_cli."""
import json
import pytest
from click.testing import CliRunner
from pipewatch.splitter_cli import splitter


@pytest.fixture
def runner():
    return CliRunner()


def test_list_rules_table_contains_headers(runner):
    result = runner.invoke(splitter, ["list-rules"])
    assert result.exit_code == 0
    assert "RULE" in result.output
    assert "PREFIX" in result.output


def test_list_rules_table_shows_rule_names(runner):
    result = runner.invoke(splitter, ["list-rules"])
    assert result.exit_code == 0
    assert "ops-all" in result.output
    assert "db-critical" in result.output


def test_list_rules_json_output_is_valid(runner):
    result = runner.invoke(splitter, ["list-rules", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) >= 1


def test_list_rules_json_contains_expected_keys(runner):
    result = runner.invoke(splitter, ["list-rules", "--format", "json"])
    data = json.loads(result.output)
    for entry in data:
        assert "name" in entry
        assert "channel_count" in entry


def test_simulate_table_shows_metric_name(runner):
    result = runner.invoke(splitter, ["simulate", "db.latency", "--status", "critical"])
    assert result.exit_code == 0
    assert "db.latency" in result.output
    assert "critical" in result.output


def test_simulate_json_output_is_valid(runner):
    result = runner.invoke(splitter, ["simulate", "db.latency", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "metric_name" in data
    assert "dispatched_to" in data
    assert "skipped_rules" in data


def test_simulate_ok_status_skips_severity_filtered_rule(runner):
    result = runner.invoke(splitter, ["simulate", "db.latency", "--status", "ok", "--format", "json"])
    data = json.loads(result.output)
    assert "db-critical" in data["skipped_rules"]
