import json
import pytest
from click.testing import CliRunner
from pipewatch.throttle_cli import throttle


@pytest.fixture
def runner():
    return CliRunner()


def test_status_table_output_contains_headers(runner):
    result = runner.invoke(throttle, ["status"])
    assert result.exit_code == 0
    assert "Metric" in result.output
    assert "Last Status" in result.output
    assert "Suppressed" in result.output


def test_status_table_shows_metric_rows(runner):
    result = runner.invoke(throttle, ["status", "--metric", "pipeline.latency"])
    assert result.exit_code == 0
    assert "pipeline.latency" in result.output


def test_status_json_output_is_valid(runner):
    result = runner.invoke(throttle, ["status", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)


def test_status_json_contains_expected_keys(runner):
    result = runner.invoke(throttle, ["status", "--format", "json", "--metric", "pipeline.errors"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1
    entry = data[0]
    assert "metric" in entry
    assert "last_status" in entry
    assert "last_notified" in entry
    assert "suppressed" in entry


def test_status_unknown_metric_shows_none(runner):
    result = runner.invoke(throttle, ["status", "--format", "json", "--metric", "unknown.metric"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data[0]["last_status"] == "none"
    assert data[0]["last_notified"] == "never"


def test_reset_outputs_confirmation(runner):
    result = runner.invoke(throttle, ["reset", "pipeline.latency"])
    assert result.exit_code == 0
    assert "pipeline.latency" in result.output
    assert "reset" in result.output.lower()
