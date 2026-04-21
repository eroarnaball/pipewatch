"""Tests for circuit_breaker_cli commands."""

import json
import pytest
from click.testing import CliRunner
from pipewatch.circuit_breaker_cli import circuit_breaker


@pytest.fixture
def runner():
    return CliRunner()


def test_status_table_contains_headers(runner):
    result = runner.invoke(circuit_breaker, ["status"])
    assert result.exit_code == 0
    assert "CHANNEL" in result.output
    assert "STATE" in result.output
    assert "FAILURES" in result.output


def test_status_table_shows_channel_rows(runner):
    result = runner.invoke(circuit_breaker, ["status"])
    assert result.exit_code == 0
    assert "slack" in result.output
    assert "pagerduty" in result.output


def test_status_json_output_is_valid(runner):
    result = runner.invoke(circuit_breaker, ["status", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) > 0


def test_status_json_contains_expected_keys(runner):
    result = runner.invoke(circuit_breaker, ["status", "--format", "json"])
    data = json.loads(result.output)
    first = data[0]
    assert "channel" in first
    assert "state" in first
    assert "failures" in first


def test_status_json_shows_open_state_for_pagerduty(runner):
    result = runner.invoke(circuit_breaker, ["status", "--format", "json"])
    data = json.loads(result.output)
    pd = next((d for d in data if d["channel"] == "pagerduty"), None)
    assert pd is not None
    assert pd["state"] == "open"


def test_reset_channel_outputs_confirmation(runner):
    result = runner.invoke(circuit_breaker, ["reset", "slack"])
    assert result.exit_code == 0
    assert "slack" in result.output
    assert "reset" in result.output


def test_detail_outputs_json(runner):
    result = runner.invoke(circuit_breaker, ["detail", "slack"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["channel"] == "slack"
