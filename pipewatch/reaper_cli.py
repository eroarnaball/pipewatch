"""CLI commands for the metric reaper."""

import json
from datetime import datetime, timedelta

import click

from pipewatch.reaper import MetricReaper, ReaperConfig
from pipewatch.history import MetricHistory, HistoryEntry
from pipewatch.metrics import MetricStatus, PipelineMetric, MetricEvaluation


def _make_entry(status: MetricStatus, minutes_ago: float = 0.0) -> HistoryEntry:
    metric = PipelineMetric(name="demo", value=1.0)
    evaluation = MetricEvaluation(metric=metric, status=status)
    entry = HistoryEntry(evaluation=evaluation)
    entry.timestamp = datetime.utcnow() - timedelta(minutes=minutes_ago)
    return entry


def _build_sample_reaper():
    config = ReaperConfig(critical_streak=3, inactive_seconds=300)
    reaper = MetricReaper(config=config)

    h_critical = MetricHistory(max_entries=50)
    for _ in range(4):
        h_critical.record(_make_entry(MetricStatus.CRITICAL))

    h_ok = MetricHistory(max_entries=50)
    for _ in range(4):
        h_ok.record(_make_entry(MetricStatus.OK))

    h_stale = MetricHistory(max_entries=50)
    h_stale.record(_make_entry(MetricStatus.WARNING, minutes_ago=20))

    return reaper, {"pipeline.critical": h_critical, "pipeline.ok": h_ok, "pipeline.stale": h_stale}


@click.group()
def reaper():
    """Metric reaper commands."""


@reaper.command("check")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]))
def check_reaper(fmt: str):
    """Evaluate all metrics and report which should be reaped."""
    r, histories = _build_sample_reaper()
    results = r.evaluate_all(histories)

    if fmt == "json":
        click.echo(json.dumps([res.to_dict() for res in results], indent=2))
        return

    if not results:
        click.echo("No metrics flagged for reaping.")
        return

    click.echo(f"{'Metric':<30} {'Reason':<20} {'Reaped At'}")
    click.echo("-" * 70)
    for res in results:
        click.echo(f"{res.metric_name:<30} {res.reason:<20} {res.reaped_at.isoformat()}")


@reaper.command("config")
def show_config():
    """Show the current reaper configuration."""
    r, _ = _build_sample_reaper()
    click.echo(json.dumps(r._config.to_dict(), indent=2))
