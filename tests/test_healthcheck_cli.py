import json
import pytest
from click.testing import CliRunner
from pipewatch.healthcheck_cli import healthcheck


@pytest.fixture()
def runner():
    return CliRunner()


def test_run_table_output_contains_header(runner):
    result = runner.invoke(healthcheck, ["run"])
    assert result.exit_code == 0
    assert "Name" in result.output
    assert "Status" in result.output


def test_run_table_output_contains_overall(runner):
    result = runner.invoke(healthcheck, ["run"])
    assert "Overall:" in result.output


def test_run_table_shows_metric_rows(runner):
    result = runner.invoke(healthcheck, ["run"])
    assert "database" in result.output
    assert "queue" in result.output
    assert "cache" in result.output


def test_run_json_output_is_valid(runner):
    result = runner.invoke(healthcheck, ["run", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, dict)


def test_run_json_contains_expected_keys(runner):
    result = runner.invoke(healthcheck, ["run", "--format", "json"])
    data = json.loads(result.output)
    assert "overall" in data
    assert "total" in data
    assert "failed_count" in data
    assert "results" in data


def test_run_json_overall_is_critical(runner):
    result = runner.invoke(healthcheck, ["run", "--format", "json"])
    data = json.loads(result.output)
    assert data["overall"] == "critical"


def test_detail_known_check(runner):
    result = runner.invoke(healthcheck, ["detail", "database"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["name"] == "database"
    assert data["status"] == "ok"


def test_detail_unknown_check_exits_nonzero(runner):
    result = runner.invoke(healthcheck, ["detail", "nonexistent"])
    assert result.exit_code != 0
    assert "No check registered" in result.output
