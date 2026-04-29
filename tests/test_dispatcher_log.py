"""Tests for pipewatch.dispatcher_log."""

from datetime import datetime

from click.testing import CliRunner

from pipewatch.dispatcher_log import DispatchRecord, DispatcherLog
from pipewatch.dispatcher_log_cli import dispatcher_log
from pipewatch.metrics import MetricStatus


def _make_record(
    name: str = "my.metric",
    status: MetricStatus = MetricStatus.WARNING,
    channel: str = "console",
    success: bool = True,
    error: str = None,
) -> DispatchRecord:
    return DispatchRecord(
        metric_name=name,
        status=status,
        channel=channel,
        message=f"{name} is {status.value}",
        dispatched_at=datetime.utcnow(),
        success=success,
        error=error,
    )


def test_record_adds_entry():
    log = DispatcherLog()
    rec = _make_record()
    log.record(rec)
    assert log.total() == 1


def test_max_entries_enforced():
    log = DispatcherLog(max_entries=3)
    for i in range(5):
        log.record(_make_record(name=f"m{i}"))
    assert log.total() == 3


def test_for_metric_filters_correctly():
    log = DispatcherLog()
    log.record(_make_record(name="a.metric"))
    log.record(_make_record(name="b.metric"))
    log.record(_make_record(name="a.metric"))
    results = log.for_metric("a.metric")
    assert len(results) == 2
    assert all(r.metric_name == "a.metric" for r in results)


def test_for_channel_filters_correctly():
    log = DispatcherLog()
    log.record(_make_record(channel="slack"))
    log.record(_make_record(channel="pagerduty"))
    results = log.for_channel("slack")
    assert len(results) == 1
    assert results[0].channel == "slack"


def test_failures_returns_only_failed():
    log = DispatcherLog()
    log.record(_make_record(success=True))
    log.record(_make_record(success=False, error="timeout"))
    assert len(log.failures()) == 1
    assert log.failures()[0].error == "timeout"


def test_by_status_filters_correctly():
    log = DispatcherLog()
    log.record(_make_record(status=MetricStatus.CRITICAL))
    log.record(_make_record(status=MetricStatus.WARNING))
    log.record(_make_record(status=MetricStatus.CRITICAL))
    assert len(log.by_status(MetricStatus.CRITICAL)) == 2


def test_to_dict_has_expected_keys():
    rec = _make_record()
    d = rec.to_dict()
    for key in ("metric_name", "status", "channel", "message", "dispatched_at", "success", "error"):
        assert key in d


def test_clear_empties_log():
    log = DispatcherLog()
    log.record(_make_record())
    log.clear()
    assert log.total() == 0


def test_cli_list_table_contains_headers():
    runner = CliRunner()
    result = runner.invoke(dispatcher_log, ["list"])
    assert result.exit_code == 0
    assert "METRIC" in result.output
    assert "CHANNEL" in result.output


def test_cli_list_json_is_valid():
    import json
    runner = CliRunner()
    result = runner.invoke(dispatcher_log, ["list", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)


def test_cli_summary_shows_counts():
    runner = CliRunner()
    result = runner.invoke(dispatcher_log, ["summary"])
    assert result.exit_code == 0
    assert "Total dispatched" in result.output
    assert "Failures" in result.output
