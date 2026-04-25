"""Tests for pipewatch.topology_cli."""
import json
import pytest
from click.testing import CliRunner
from pipewatch.topology_cli import topology


@pytest.fixture
def runner():
    return CliRunner()


def test_show_table_contains_headers(runner):
    result = runner.invoke(topology, ["show"])
    assert result.exit_code == 0
    assert "NODE" in result.output
    assert "TAGS" in result.output
    assert "SOURCE" in result.output
    assert "TARGET" in result.output


def test_show_table_contains_node_names(runner):
    result = runner.invoke(topology, ["show"])
    assert result.exit_code == 0
    assert "ingest" in result.output
    assert "transform" in result.output
    assert "load" in result.output


def test_show_json_output_is_valid(runner):
    result = runner.invoke(topology, ["show", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "nodes" in data
    assert "edges" in data


def test_show_json_contains_expected_counts(runner):
    result = runner.invoke(topology, ["show", "--format", "json"])
    data = json.loads(result.output)
    assert len(data["nodes"]) == 4
    assert len(data["edges"]) == 3


def test_neighbors_known_metric(runner):
    result = runner.invoke(topology, ["neighbors", "ingest"])
    assert result.exit_code == 0
    assert "transform" in result.output


def test_neighbors_unknown_metric_shows_message(runner):
    result = runner.invoke(topology, ["neighbors", "nonexistent"])
    assert result.exit_code == 0
    assert "No downstream" in result.output


def test_reachable_table_output(runner):
    result = runner.invoke(topology, ["reachable", "ingest"])
    assert result.exit_code == 0
    assert "transform" in result.output
    assert "load" in result.output
    assert "report" in result.output


def test_reachable_json_output(runner):
    result = runner.invoke(topology, ["reachable", "ingest", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["start"] == "ingest"
    assert "transform" in data["reachable"]


def test_reachable_leaf_node_shows_message(runner):
    result = runner.invoke(topology, ["reachable", "report"])
    assert result.exit_code == 0
    assert "No nodes reachable" in result.output
