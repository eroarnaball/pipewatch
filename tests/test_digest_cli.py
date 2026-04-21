"""Tests for pipewatch.digest_cli module."""

import json
import pytest
from click.testing import CliRunner
from pipewatch.digest_cli import digest


@pytest.fixture
def runner():
    return CliRunner()


def test_show_table_output_contains_summary_header(runner):
    result = runner.invoke(digest, ["show"])
    assert result.exit_code == 0
    assert "Digest Summary" in result.output


def test_show_table_output_contains_counts(runner):
    result = runner.invoke(digest, ["show"])
    assert "OK:" in result.output
    assert "Warning:" in result.output
    assert "Critical:" in result.output


def test_show_table_output_contains_avg_score(runner):
    result = runner.invoke(digest, ["show"])
    assert "Avg Score:" in result.output


def test_show_json_output_is_valid(runner):
    result = runner.invoke(digest, ["show", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, dict)


def test_show_json_contains_expected_keys(runner):
    result = runner.invoke(digest, ["show", "--format", "json"])
    data = json.loads(result.output)
    for key in ("ok_count", "warning_count", "critical_count", "avg_score", "top_issues", "timestamp"):
        assert key in data


def test_show_json_top_issues_is_list(runner):
    result = runner.invoke(digest, ["show", "--format", "json"])
    data = json.loads(result.output)
    assert isinstance(data["top_issues"], list)


def test_show_max_issues_option_limits_output(runner):
    result = runner.invoke(digest, ["show", "--format", "json", "--max-issues", "1"])
    data = json.loads(result.output)
    assert len(data["top_issues"]) <= 1
