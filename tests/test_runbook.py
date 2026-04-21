"""Tests for pipewatch.runbook and runbook_cli."""

import json
import pytest
from click.testing import CliRunner
from pipewatch.runbook import RunbookRegistry, RunbookEntry
from import MetricStatus
from pipewatch.runbook_cli import runbook


def make_registry() -> RunbookRegistry:
    reg = RunbookRegistry()
    reg.register("cpu", MetricStatus.WARNING, "CPU high", ["Check processes", "Scale up"])
    reg.register("cpu", MetricStatus.CRITICAL, "CPU critical", ["Kill runaway process"])
    return reg


def test_register_returns_entry():
    reg = RunbookRegistry()
    entry = reg.register("latency", MetricStatus.WARNING, "High latency", ["Restart service"])
    assert isinstance(entry, RunbookEntry)
    assert entry.metric_name == "latency"
    assert entry.status == MetricStatus.WARNING


def test_lookup_returns_correct_entry():
    reg = make_registry()
    entry = reg.lookup("cpu", MetricStatus.WARNING)
    assert entry is not None
    assert entry.title == "CPU high"
    assert "Check processes" in entry.steps


def test_lookup_returns_none_for_missing():
    reg = make_registry()
    assert reg.lookup("cpu", MetricStatus.OK) is None
    assert reg.lookup("unknown", MetricStatus.WARNING) is None


def test_all_entries_returns_all():
    reg = make_registry()
    entries = reg.all_entries()
    assert len(entries) == 2


def test_remove_deletes_entry():
    reg = make_registry()
    removed = reg.remove("cpu", MetricStatus.WARNING)
    assert removed is True
    assert reg.lookup("cpu", MetricStatus.WARNING) is None


def test_remove_returns_false_for_unknown():
    reg = make_registry()
    assert reg.remove("nonexistent", MetricStatus.OK) is False


def test_to_dict_has_expected_keys():
    reg = make_registry()
    entry = reg.lookup("cpu", MetricStatus.CRITICAL)
    d = entry.to_dict()
    assert set(d.keys()) == {"metric_name", "status", "title", "steps"}
    assert d["status"] == "critical"


def test_cli_list_table_output():
    runner = CliRunner()
    result = runner.invoke(runbook, ["list"])
    assert result.exit_code == 0
    assert "METRIC" in result.output
    assert "row_count" in result.output


def test_cli_list_json_output():
    runner = CliRunner()
    result = runner.invoke(runbook, ["list", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert all("metric_name" in e for e in data)


def test_cli_lookup_known_entry():
    runner = CliRunner()
    result = runner.invoke(runbook, ["lookup", "row_count", "warning"])
    assert result.exit_code == 0
    assert "Row count below expected range" in result.output


def test_cli_lookup_unknown_entry_exits_nonzero():
    runner = CliRunner()
    result = runner.invoke(runbook, ["lookup", "nonexistent", "warning"])
    assert result.exit_code != 0


def test_cli_lookup_invalid_status_exits_nonzero():
    runner = CliRunner()
    result = runner.invoke(runbook, ["lookup", "row_count", "banana"])
    assert result.exit_code != 0
