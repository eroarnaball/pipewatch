"""CLI commands for sliding window aggregation."""

import json
from datetime import datetime, timedelta

import click

from pipewatch.history import HistoryEntry, MetricHistory
from pipewatch.metrics import MetricStatus
from pipewatch.window_aggregator import WindowAggregator


def _build_sample_history() -> MetricHistory:
    history = MetricHistory(max_entries=200)
    now = datetime.utcnow()
    statuses = [
        MetricStatus.OK, MetricStatus.OK, MetricStatus.WARNING,
        MetricStatus.OK, MetricStatus.CRITICAL, MetricStatus.OK,
    ]
    for i, status in enumerate(statuses):
        entry = HistoryEntry(
            metric_name="pipeline.latency",
            status=status,
            value=float(10 + i * 3),
            timestamp=now - timedelta(seconds=30 * (len(statuses) - i)),
        )
        history.record(entry)
    return history


@click.group()
def window():
    """Sliding window aggregation commands."""


@window.command("stats")
@click.argument("metric_name")
@click.option("--window", "window_seconds", default=300, show_default=True,
              help="Window size in seconds.")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]),
              show_default=True)
def show_stats(metric_name: str, window_seconds: int, fmt: str):
    """Show aggregated stats for a metric within a sliding time window."""
    history = _build_sample_history()
    aggregator = WindowAggregator(window_seconds=window_seconds)
    stats = aggregator.compute(metric_name, history)

    if stats is None:
        click.echo(f"No history found for metric: {metric_name}")
        raise SystemExit(1)

    if fmt == "json":
        click.echo(json.dumps(stats.to_dict(), indent=2))
    else:
        click.echo(f"Window Stats — {metric_name} (last {window_seconds}s)")
        click.echo(f"  Count    : {stats.count}")
        click.echo(f"  OK       : {stats.ok_count}")
        click.echo(f"  Warning  : {stats.warning_count}")
        click.echo(f"  Critical : {stats.critical_count}")
        if stats.avg_value is not None:
            click.echo(f"  Avg Value: {stats.avg_value:.2f}")
            click.echo(f"  Min Value: {stats.min_value:.2f}")
            click.echo(f"  Max Value: {stats.max_value:.2f}")
        else:
            click.echo("  No numeric values in window.")
