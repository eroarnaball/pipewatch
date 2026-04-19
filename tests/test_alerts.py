"""Tests for alert dispatch and channels."""

import pytest
from pipewatch.alerts import AlertDispatcher, AlertMessage, ConsoleAlertChannel
from pipewatch.metrics import MetricEvaluation, MetricStatus, PipelineMetric


def make_evaluation(value: float, status: MetricStatus, msg: str = "") -> MetricEvaluation:
    metric = PipelineMetric(pipeline="pipe1", name="row_count", value=value)
    return MetricEvaluation(metric=metric, status=status, message=msg)


def test_alert_message_format():
    msg = AlertMessage(
        pipeline="pipe1", metric="row_count",
        status=MetricStatus.CRITICAL, value=5.0, message="Too low"
    )
    formatted = msg.format()
    assert "CRITICAL" in formatted
    assert "pipe1" in formatted
    assert "row_count" in formatted
    assert "5.0" in formatted


def test_dispatcher_skips_ok(capsys):
    channel = ConsoleAlertChannel()
    dispatcher = AlertDispatcher(channels=[channel])
    ev = make_evaluation(100.0, MetricStatus.OK)
    dispatcher.dispatch(ev)
    captured = capsys.readouterr()
    assert captured.out == ""


def test_dispatcher_sends_warning(capsys):
    channel = ConsoleAlertChannel()
    dispatcher = AlertDispatcher(channels=[channel])
    ev = make_evaluation(80.0, MetricStatus.WARNING, "Near threshold")
    dispatcher.dispatch(ev)
    captured = capsys.readouterr()
    assert "WARNING" in captured.out


def test_dispatcher_sends_critical(capsys):
    channel = ConsoleAlertChannel()
    dispatcher = AlertDispatcher(channels=[channel])
    ev = make_evaluation(10.0, MetricStatus.CRITICAL, "Critical failure")
    dispatcher.dispatch(ev)
    captured = capsys.readouterr()
    assert "CRITICAL" in captured.out


def test_dispatch_all(capsys):
    channel = ConsoleAlertChannel()
    dispatcher = AlertDispatcher(channels=[channel])
    evs = [
        make_evaluation(100.0, MetricStatus.OK),
        make_evaluation(80.0, MetricStatus.WARNING, "warn"),
        make_evaluation(5.0, MetricStatus.CRITICAL, "crit"),
    ]
    dispatcher.dispatch_all(evs)
    captured = capsys.readouterr()
    assert "WARNING" in captured.out
    assert "CRITICAL" in captured.out


def test_add_channel():
    dispatcher = AlertDispatcher()
    assert len(dispatcher.channels) == 0
    dispatcher.add_channel(ConsoleAlertChannel())
    assert len(dispatcher.channels) == 1
