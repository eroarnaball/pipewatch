import json

import pytest
from click.testing import CliRunner

from pipewatch.recurrence_cli import recurrence


@pytest.fixture
def runner():
    return CliRunner()


def test_show_table_contains_headers(runner):
    result = runner.invoke(recurrence, ["show"])
    assert result.exit_code == 0
    assert "Metric" in result.output
    assert "Status" in result.output
    assert "Count" in result.output


def test_show_table_contains_recurring_metric(runner):
    result = runner.invoke(recurrence, ["show"])
    assert result.exit_code == 0
    # orders.lag fires 4 times with threshold=3 in sample
    assert "orders.lag" in result.output


def test_show_json_output_is_valid(runner):
    result = runner.invoke(recurrence, ["show", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)


def test_show_json_contains_expected_keys(runner):
    result = runner.invoke(recurrence, ["show", "--format", "json"])
    data = json.loads(result.output)
    assert len(data) > 0
    entry = data[0]
    assert "metric_name" in entry
    assert "status" in entry
    assert "count" in entry
    assert "first_seen" in entry
    assert "last_seen" in entry


def test_show_json_excludes_non_recurring(runner):
    result = runner.invoke(recurrence, ["show", "--format", "json"])
    data = json.loads(result.output)
    names = [e["metric_name"] for e in data]
    # queue.depth only fires once, threshold=3 — should not appear
    assert "queue.depth" not in names


def test_check_known_metric_table(runner):
    result = runner.invoke(recurrence, ["check", "orders.lag"])
    assert result.exit_code == 0
    assert "orders.lag" in result.output
    assert "Count" in result.output


def test_check_known_metric_json(runner):
    result = runner.invoke(recurrence, ["check", "orders.lag", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["metric_name"] == "orders.lag"
    assert data["is_recurring"] is True


def test_check_unknown_metric_exits_nonzero(runner):
    result = runner.invoke(recurrence, ["check", "nonexistent.metric"])
    assert result.exit_code != 0
