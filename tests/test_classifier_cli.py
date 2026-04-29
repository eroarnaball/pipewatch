"""Tests for pipewatch.classifier_cli."""
from __future__ import annotations
import json
import pytest
from click.testing import CliRunner
from pipewatch.classifier_cli import classifier


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_list_table_output_contains_headers(runner):
    result = runner.invoke(classifier, ["list"])
    assert result.exit_code == 0
    assert "METRIC" in result.output
    assert "STATUS" in result.output
    assert "CLASS" in result.output


def test_list_table_shows_metric_rows(runner):
    result = runner.invoke(classifier, ["list"])
    assert result.exit_code == 0
    assert "latency" in result.output
    assert "error_rate" in result.output


def test_list_json_output_is_valid(runner):
    result = runner.invoke(classifier, ["list", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) > 0


def test_list_json_contains_expected_keys(runner):
    result = runner.invoke(classifier, ["list", "--format", "json"])
    data = json.loads(result.output)
    for entry in data:
        assert "metric_name" in entry
        assert "matched_class" in entry
        assert "status" in entry
        assert "value" in entry


def test_list_json_unclassified_metric_has_null_class(runner):
    result = runner.invoke(classifier, ["list", "--format", "json"])
    data = json.loads(result.output)
    ok_entries = [e for e in data if e["status"] == "ok"]
    assert all(e["matched_class"] is None for e in ok_entries)


def test_rules_table_output_contains_headers(runner):
    result = runner.invoke(classifier, ["rules"])
    assert result.exit_code == 0
    assert "RULE" in result.output
    assert "STATUS" in result.output


def test_rules_json_output_is_valid(runner):
    result = runner.invoke(classifier, ["rules", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) > 0


def test_rules_json_contains_expected_keys(runner):
    result = runner.invoke(classifier, ["rules", "--format", "json"])
    data = json.loads(result.output)
    for rule in data:
        assert "name" in rule
        assert "status" in rule
        assert "min_value" in rule
        assert "max_value" in rule
