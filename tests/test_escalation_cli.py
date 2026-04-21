"""Tests for pipewatch.escalation_cli."""

import json
from click.testing import CliRunner

from pipewatch.escalation_cli import escalation


def test_simulate_table_output_contains_headers():
    runner = CliRunner()
    result = runner.invoke(escalation, ["simulate", "--warnings", "3"])
    assert result.exit_code == 0
    assert "Status" in result.output
    assert "Effective" in result.output
    assert "Escalated" in result.output


def test_simulate_json_output_is_valid():
    runner = CliRunner()
    result = runner.invoke(escalation, ["simulate", "--warnings", "4", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 4


def test_simulate_json_contains_expected_keys():
    runner = CliRunner()
    result = runner.invoke(escalation, ["simulate", "--warnings", "2", "--format", "json"])
    data = json.loads(result.output)
    for entry in data:
        assert "metric_name" in entry
        assert "original_status" in entry
        assert "effective_status" in entry
        assert "escalated" in entry


def test_simulate_escalation_flag_set_after_threshold():
    runner = CliRunner()
    result = runner.invoke(escalation, ["simulate", "--warnings", "5", "--format", "json"])
    data = json.loads(result.output)
    # default escalate_after=3, so entries 3+ should be escalated
    assert data[2]["escalated"] is True
    assert data[2]["effective_status"] == "critical"


def test_policy_command_outputs_json():
    runner = CliRunner()
    result = runner.invoke(escalation, ["policy", "--after", "5", "--window", "600"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["escalate_after"] == 5
    assert data["escalate_window"] == 600
