"""Tests for pipewatch.scorer_cli."""

from click.testing import CliRunner
from pipewatch.scorer_cli import scorer


def test_score_table_output():
    runner = CliRunner()
    result = runner.invoke(scorer, ["score"])
    assert result.exit_code == 0
    assert "Health Score" in result.output
    assert "Grade" in result.output


def test_score_json_output():
    import json
    runner = CliRunner()
    result = runner.invoke(scorer, ["score", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "percentage" in data
    assert "grade" in data
    assert "metric_scores" in data


def test_score_with_custom_weight():
    runner = CliRunner()
    result = runner.invoke(scorer, ["score", "-w", "row_count:3.0"])
    assert result.exit_code == 0
    assert "row_count" in result.output


def test_score_invalid_weight_format_ignored():
    runner = CliRunner()
    result = runner.invoke(scorer, ["score", "-w", "bad_entry"])
    assert result.exit_code == 0


def test_grade_command():
    runner = CliRunner()
    result = runner.invoke(scorer, ["grade"])
    assert result.exit_code == 0
    assert "Health grade" in result.output
    assert any(g in result.output for g in ["A", "B", "C", "D", "F"])
