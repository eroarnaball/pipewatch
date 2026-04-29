"""Tests for pipewatch.normalizer_cli."""

import json
import pytest
from click.testing import CliRunner
from pipewatch.normalizer_cli import normalizer


@pytest.fixture
def runner():
    return CliRunner()


def test_show_table_contains_headers(runner):
    result = runner.invoke(normalizer, ["show"])
    assert result.exit_code == 0
    assert "Metric" in result.output
    assert "Min" in result.output
    assert "Max" in result.output


def test_show_table_contains_metric_rows(runner):
    result = runner.invoke(normalizer, ["show"])
    assert result.exit_code == 0
    assert "latency_ms" in result.output
    assert "error_rate" in result.output
    assert "queue_depth" in result.output


def test_show_json_output_is_valid(runner):
    result = runner.invoke(normalizer, ["show", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, dict)


def test_show_json_contains_expected_keys(runner):
    result = runner.invoke(normalizer, ["show", "--format", "json"])
    data = json.loads(result.output)
    for key in data:
        assert "min" in data[key]
        assert "max" in data[key]


def test_normalize_known_metric_table(runner):
    result = runner.invoke(normalizer, ["normalize", "latency_ms", "1000.0"])
    assert result.exit_code == 0
    assert "latency_ms" in result.output
    assert "Normalized" in result.output


def test_normalize_known_metric_json(runner):
    result = runner.invoke(normalizer, ["normalize", "latency_ms", "1000.0", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["metric"] == "latency_ms"
    assert "normalized" in data
    assert "raw" in data


def test_normalize_unknown_metric_exits_nonzero(runner):
    result = runner.invoke(normalizer, ["normalize", "does_not_exist", "42.0"])
    assert result.exit_code != 0


def test_normalize_midpoint_value(runner):
    result = runner.invoke(normalizer, ["normalize", "error_rate", "0.5", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert abs(data["normalized"] - 0.5) < 1e-4
