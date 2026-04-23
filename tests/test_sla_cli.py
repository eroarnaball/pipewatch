import json
import pytest
from click.testing import CliRunner
from pipewatch.sla_cli import sla


@pytest.fixture
def runner():
    return CliRunner()


def test_check_table_output_contains_headers(runner):
    result = runner.invoke(sla, ["check"])
    assert result.exit_code == 0
    assert "Metric" in result.output
    assert "Crit%" in result.output
    assert "Warn%" in result.output


def test_check_table_shows_metric_rows(runner):
    result = runner.invoke(sla, ["check"])
    assert result.exit_code == 0
    assert "orders" in result.output
    assert "payments" in result.output


def test_check_json_output_is_valid(runner):
    result = runner.invoke(sla, ["check", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, dict)


def test_check_json_contains_expected_keys(runner):
    result = runner.invoke(sla, ["check", "--format", "json"])
    data = json.loads(result.output)
    for metric_data in data.values():
        assert "critical_ratio" in metric_data
        assert "warning_ratio" in metric_data
        assert "critical_breached" in metric_data
        assert "warning_breached" in metric_data
        assert "any_breached" in metric_data


def test_detail_known_metric(runner):
    result = runner.invoke(sla, ["detail", "orders"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["metric_name"] == "orders"


def test_detail_unknown_metric_exits_nonzero(runner):
    result = runner.invoke(sla, ["detail", "nonexistent_metric"])
    assert result.exit_code != 0
