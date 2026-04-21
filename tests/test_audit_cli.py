import json
import pytest
from click.testing import CliRunner
from pipewatch.audit_cli import audit


@pytest.fixture
def runner():
    return CliRunner()


def test_list_table_output_contains_headers(runner):
    result = runner.invoke(audit, ["list"])
    assert result.exit_code == 0
    assert "EVENT TYPE" in result.output
    assert "METRIC" in result.output
    assert "TIMESTAMP" in result.output


def test_list_table_shows_entries(runner):
    result = runner.invoke(audit, ["list"])
    assert result.exit_code == 0
    assert "cpu_usage" in result.output
    assert "memory" in result.output


def test_list_json_output_is_valid(runner):
    result = runner.invoke(audit, ["list", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) > 0


def test_list_json_contains_expected_keys(runner):
    result = runner.invoke(audit, ["list", "--format", "json"])
    data = json.loads(result.output)
    entry = data[0]
    assert "event_type" in entry
    assert "metric_name" in entry
    assert "timestamp" in entry
    assert "details" in entry


def test_list_filter_by_metric(runner):
    result = runner.invoke(audit, ["list", "--metric", "memory"])
    assert result.exit_code == 0
    assert "memory" in result.output
    assert "disk_io" not in result.output


def test_list_filter_by_event_type(runner):
    result = runner.invoke(audit, ["list", "--event-type", "ALERT_SENT"])
    assert result.exit_code == 0
    assert "ALERT_SENT" in result.output


def test_list_invalid_event_type_exits_nonzero(runner):
    result = runner.invoke(audit, ["list", "--event-type", "NOT_REAL"])
    assert result.exit_code != 0


def test_list_limit_respected(runner):
    result = runner.invoke(audit, ["list", "--format", "json", "--limit", "2"])
    data = json.loads(result.output)
    assert len(data) <= 2


def test_summary_shows_event_types(runner):
    result = runner.invoke(audit, ["summary"])
    assert result.exit_code == 0
    assert "EVENT TYPE" in result.output
    assert "COUNT" in result.output


def test_summary_counts_are_positive(runner):
    result = runner.invoke(audit, ["summary"])
    lines = [l for l in result.output.strip().splitlines() if l and not l.startswith("-") and "EVENT" not in l]
    for line in lines:
        parts = line.split()
        assert int(parts[-1]) > 0
