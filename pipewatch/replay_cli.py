"""CLI commands for replaying metric history."""

import click
from pipewatch.history import MetricHistory, HistoryEntry
from pipewatch.metrics import MetricStatus, PipelineMetric
from pipewatch.replay import MetricReplayer
from datetime import datetime, timezone


def _build_sample_history() -> MetricHistory:
    h = MetricHistory(max_entries=20)
    values = [10, 45, 80, 55, 90, 30, 70, 20]
    statuses = [
        MetricStatus.OK, MetricStatus.WARNING, MetricStatus.CRITICAL,
        MetricStatus.WARNING, MetricStatus.CRITICAL, MetricStatus.OK,
        MetricStatus.WARNING, MetricStatus.OK,
    ]
    for v, s in zip(values, statuses):
        m = PipelineMetric(name="demo", value=v, unit="ms")
        from pipewatch.metrics import MetricEvaluation
        ev = MetricEvaluation(metric=m, status=s, message=f"value={v}")
        h.record(ev)
    return h


@click.group()
def replay():
    """Replay and inspect metric history."""


@replay.command("summary")
def replay_summary():
    """Show summary of recorded metric history."""
    h = _build_sample_history()
    r = MetricReplayer(h)
    s = r.summary()
    click.echo(f"Total frames : {s['total']}")
    click.echo(f"OK           : {s['ok']}")
    click.echo(f"Warning      : {s['warning']}")
    click.echo(f"Critical     : {s['critical']}")


@replay.command("first")
@click.argument("status", type=click.Choice(["ok", "warning", "critical"]))
def first_occurrence(status):
    """Find first frame with given STATUS."""
    h = _build_sample_history()
    r = MetricReplayer(h)
    st = MetricStatus[status.upper()]
    frame = r.first_occurrence(st)
    if frame is None:
        click.echo(f"No frame with status {status}.")
    else:
        click.echo(f"First {status} at index {frame.index}: {frame.entry.to_dict()}")


@replay.command("slice")
@click.argument("start", type=int)
@click.argument("end", type=int)
def replay_slice(start, end):
    """Show frames from START to END."""
    h = _build_sample_history()
    r = MetricReplayer(h)
    frames = r.slice(start, end)
    for f in frames:
        click.echo(f"[{f.index}] {f.entry.status.value} — {f.entry.evaluation.metric.value}")
