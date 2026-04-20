"""Tests for pipewatch.enricher_cli."""

from click.testing import CliRunner
import json

from pipewatch.enricher_cli import enricher


def test_list_table_output_contains_headers():
    runner = CliRunner()
    result = runner.invoke(enricher, ["list"])
    assert result.exit_code == 0
    assert "Metric" in result.output
    assert "Status" in result.output
    assert "Score" in result.output


def test_list_table_contains_metric_names():
    runner = CliRunner()
    result = runner.invoke(enricher, ["list"])
    assert "row_count" in result.output
    assert "error_rate" in result.output
    assert "latency_p99" in result.output


def test_list_json_output_is_valid():
    runner = CliRunner()
    result = runner.invoke(enricher, ["list", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 3


def test_list_json_contains_expected_keys():
    runner = CliRunner()
    result = runner.invoke(enricher, ["list", "--format", "json"])
    data = json.loads(result.output)
    for entry in data:
        assert "metric" in entry
        assert "status" in entry
        assert "is_critical" in entry
        assert "severity_score" in entry
        assert "label" in entry


def test_list_json_critical_metric_flagged():
    runner = CliRunner()
    result = runner.invoke(enricher, ["list", "--format", "json"])
    data = json.loads(result.output)
    critical = [e for e in data if e["metric"] == "latency_p99"]
    assert len(critical) == 1
    assert critical[0]["is_critical"] is True
    assert critical[0]["severity_score"] == 2
