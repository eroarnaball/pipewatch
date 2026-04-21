import json
import pytest
from click.testing import CliRunner
from pipewatch.ratelimiter_cli import ratelimiter


@pytest.fixture
def runner():
    return CliRunner()


def test_status_table_contains_headers(runner):
    result = runner.invoke(ratelimiter, ["status"])
    assert result.exit_code == 0
    assert "Metric" in result.output
    assert "Max" in result.output
    assert "Window" in result.output


def test_status_table_shows_metric_rows(runner):
    result = runner.invoke(ratelimiter, ["status"])
    assert result.exit_code == 0
    assert "row_count" in result.output
    assert "latency_p99" in result.output


def test_status_json_output_is_valid(runner):
    result = runner.invoke(ratelimiter, ["status", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)


def test_status_json_contains_expected_keys(runner):
    result = runner.invoke(ratelimiter, ["status", "--format", "json"])
    data = json.loads(result.output)
    assert len(data) > 0
    for entry in data:
        assert "metric_name" in entry
        assert "max_alerts" in entry
        assert "window_seconds" in entry
        assert "is_limited" in entry
        assert "remaining" in entry


def test_status_shows_limited_for_exhausted_metric(runner):
    result = runner.invoke(ratelimiter, ["status", "--format", "json"])
    data = json.loads(result.output)
    row_count = next((e for e in data if e["metric_name"] == "row_count"), None)
    assert row_count is not None
    assert row_count["is_limited"] is True


def test_reset_unknown_metric_exits_nonzero(runner):
    result = runner.invoke(ratelimiter, ["reset", "nonexistent_metric_xyz"])
    assert result.exit_code != 0
