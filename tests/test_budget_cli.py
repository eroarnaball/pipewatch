"""Tests for pipewatch.budget_cli module."""
from click.testing import CliRunner
from pipewatch.budget_cli import budget


def test_check_table_output():
    runner = CliRunner()
    result = runner.invoke(budget, ["check"])
    assert result.exit_code == 0
    assert "Metric" in result.output
    assert "latency" in result.output
    assert "error_rate" in result.output
    assert "throughput" in result.output


def test_check_json_output():
    import json
    runner = CliRunner()
    result = runner.invoke(budget, ["check", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 3
    assert "metric_name" in data[0]
    assert "critical_ratio" in data[0]
    assert "warning_budget_exceeded" in data[0]


def test_check_shows_exceeded_status():
    runner = CliRunner()
    result = runner.invoke(budget, ["check"])
    assert result.exit_code == 0
    # error_rate has 3/10 critical which exceeds 0.05 threshold
    assert "EXCEEDED" in result.output or "OK" in result.output


def test_detail_known_metric():
    import json
    runner = CliRunner()
    result = runner.invoke(budget, ["detail", "latency"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["metric_name"] == "latency"
    assert "window_size" in data
    assert "critical_budget_exceeded" in data


def test_detail_unknown_metric_exits_nonzero():
    runner = CliRunner()
    result = runner.invoke(budget, ["detail", "nonexistent_metric"])
    assert result.exit_code != 0
