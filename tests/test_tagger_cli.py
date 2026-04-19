"""Tests for pipewatch.tagger_cli."""
from click.testing import CliRunner
from pipewatch.tagger_cli import tagger


def test_list_all_metrics():
    runner = CliRunner()
    result = runner.invoke(tagger, ["list"])
    assert result.exit_code == 0
    assert "cpu_usage" in result.output
    assert "mem_usage" in result.output


def test_list_filter_by_key():
    runner = CliRunner()
    result = runner.invoke(tagger, ["list", "--tag-key", "env"])
    assert result.exit_code == 0
    assert "cpu_usage" in result.output


def test_list_filter_by_key_and_value():
    runner = CliRunner()
    result = runner.invoke(tagger, ["list", "--tag-key", "env", "--tag-value", "staging"])
    assert result.exit_code == 0
    assert "error_rate" in result.output
    assert "cpu_usage" not in result.output


def test_list_no_results_message():
    runner = CliRunner()
    result = runner.invoke(tagger, ["list", "--tag-key", "nonexistent"])
    assert result.exit_code == 0
    assert "No metrics found" in result.output


def test_keys_lists_all_tag_keys():
    runner = CliRunner()
    result = runner.invoke(tagger, ["keys"])
    assert result.exit_code == 0
    assert "env" in result.output
    assert "team" in result.output
