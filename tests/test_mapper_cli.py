"""Tests for pipewatch.mapper_cli."""
import json
import pytest
from click.testing import CliRunner
from pipewatch.mapper_cli import mapper


@pytest.fixture
def runner():
    return CliRunner()


def test_list_table_contains_headers(runner):
    result = runner.invoke(mapper, ["list"])
    assert result.exit_code == 0
    assert "CANONICAL" in result.output
    assert "ALIASES" in result.output


def test_list_table_shows_metric_rows(runner):
    result = runner.invoke(mapper, ["list"])
    assert "row_count" in result.output
    assert "latency_ms" in result.output


def test_list_table_shows_aliases(runner):
    result = runner.invoke(mapper, ["list"])
    assert "rows" in result.output
    assert "latency" in result.output


def test_list_json_output_is_valid(runner):
    result = runner.invoke(mapper, ["list", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) > 0


def test_list_json_contains_expected_keys(runner):
    result = runner.invoke(mapper, ["list", "--format", "json"])
    data = json.loads(result.output)
    for entry in data:
        assert "canonical" in entry
        assert "aliases" in entry
        assert "description" in entry


def test_resolve_known_alias(runner):
    result = runner.invoke(mapper, ["resolve", "rows"])
    assert result.exit_code == 0
    assert "row_count" in result.output


def test_resolve_canonical_name(runner):
    result = runner.invoke(mapper, ["resolve", "latency_ms"])
    assert result.exit_code == 0
    assert "latency_ms" in result.output


def test_resolve_unknown_exits_nonzero(runner):
    result = runner.invoke(mapper, ["resolve", "totally_unknown_metric"])
    assert result.exit_code != 0
