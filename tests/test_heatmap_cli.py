from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from pipewatch.heatmap_cli import heatmap


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_show_table_contains_header(runner):
    result = runner.invoke(heatmap, ["show", "pipeline.lag"])
    assert result.exit_code == 0
    assert "Heatmap" in result.output
    assert "Hour" in result.output


def test_show_table_contains_24_rows(runner):
    result = runner.invoke(heatmap, ["show", "pipeline.lag"])
    assert result.exit_code == 0
    # Each hour 0-23 should appear
    for hour in range(24):
        assert str(hour) in result.output


def test_show_json_output_is_valid(runner):
    result = runner.invoke(heatmap, ["show", "pipeline.lag", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "metric_name" in data
    assert "cells" in data


def test_show_json_has_24_cells(runner):
    result = runner.invoke(heatmap, ["show", "pipeline.errors", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data["cells"]) == 24


def test_show_unknown_metric_exits_nonzero(runner):
    result = runner.invoke(heatmap, ["show", "does.not.exist"])
    assert result.exit_code != 0


def test_all_table_output_lists_metrics(runner):
    result = runner.invoke(heatmap, ["all"])
    assert result.exit_code == 0
    assert "pipeline.lag" in result.output
    assert "pipeline.errors" in result.output


def test_all_json_output_is_valid_list(runner):
    result = runner.invoke(heatmap, ["all", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 2
    assert all("metric_name" in item for item in data)
