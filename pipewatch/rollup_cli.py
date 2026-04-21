"""CLI commands for inspecting metric rollup windows."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import click

from pipewatch.rollup import MetricRollup
from pipewatch.history import MetricHistory, HistoryEntry
from pipewatch.metrics import MetricStatus


def _build_sample_rollup() -> MetricRollup:
    rollup = MetricRollup(window_seconds=300)
    now = datetime.utcnow()

    for name, statuses, values in [
        ("row_count", [MetricStatus.OK, MetricStatus.WARNING, MetricStatus.OK], [120.0, 95.0, 130.0]),
        ("latency_ms", [MetricStatus.CRITICAL, MetricStatus.CRITICAL, MetricStatus.WARNING], [980.0, 1050.0, 750.0]),
    ]:
        history = MetricHistory(max_entries=50)
        for i, (status, value) in enumerate(zip(statuses, values)):
            entry = HistoryEntry(
                metric_name=name,
                status=status,
                value=value,
                timestamp=now - timedelta(seconds=60 * (len(statuses) - i)),
            )
            history.record(entry)
        rollup.register(name, history)

    return rollup


@click.group()
def rollup() -> None:
    """Inspect metric rollup summaries over time windows."""


@rollup.command("show")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]), show_default=True)
@click.option("--window", default=300, show_default=True, help="Window size in seconds.")
def show_rollup(fmt: str, window: int) -> None:
    """Show rollup summaries for all registered metrics."""
    r = _build_sample_rollup()
    r.window_seconds = window
    results = r.compute_all()

    if fmt == "json":
        click.echo(json.dumps([v.to_dict() for v in results.values()], indent=2))
        return

    click.echo(f"{'Metric':<20} {'Total':>6} {'OK':>6} {'WARN':>6} {'CRIT':>6} {'Avg':>10}")
    click.echo("-" * 60)
    for window_obj in results.values():
        avg = f"{window_obj.avg_value:.2f}" if window_obj.avg_value is not None else "N/A"
        click.echo(
            f"{window_obj.metric_name:<20} {window_obj.total:>6} "
            f"{window_obj.ok_count:>6} {window_obj.warning_count:>6} "
            f"{window_obj.critical_count:>6} {avg:>10}"
        )
