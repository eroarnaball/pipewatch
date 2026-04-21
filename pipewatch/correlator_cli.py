"""CLI commands for metric correlation analysis."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import click

from pipewatch.correlator import MetricCorrelator
from pipewatch.history import HistoryEntry, MetricHistory
from pipewatch.metrics import MetricStatus


def _build_sample_correlator() -> MetricCorrelator:
    correlator = MetricCorrelator()
    now = datetime.now(timezone.utc).timestamp()

    def _history(statuses):
        h = MetricHistory(max_entries=50)
        for i, st in enumerate(statuses):
            h.record(
                HistoryEntry(
                    metric_name="",
                    status=st,
                    value=float(i),
                    timestamp=now - (len(statuses) - i) * 30,
                )
            )
        return h

    pattern = [
        MetricStatus.OK, MetricStatus.WARNING, MetricStatus.CRITICAL,
        MetricStatus.WARNING, MetricStatus.OK,
    ]
    correlator.register("ingestion_lag", _history(pattern))
    correlator.register("queue_depth", _history(pattern))
    correlator.register("error_rate", _history(
        [MetricStatus.OK, MetricStatus.OK, MetricStatus.OK,
         MetricStatus.OK, MetricStatus.OK]
    ))
    return correlator


@click.group()
def correlator():
    """Metric correlation commands."""


@correlator.command("top")
@click.option("--window", default=60.0, show_default=True, help="Co-occurrence window in seconds.")
@click.option("--min-score", default=0.5, show_default=True, help="Minimum correlation score.")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]), show_default=True)
def top_correlations(window: float, min_score: float, fmt: str) -> None:
    """Show top correlated metric pairs."""
    c = _build_sample_correlator()
    results = c.top_correlations(window_seconds=window, min_score=min_score)

    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
        return

    if not results:
        click.echo("No correlated pairs found.")
        return

    click.echo(f"{'Metric A':<20} {'Metric B':<20} {'Score':>7} {'Co-occ':>7} {'Total':>7}")
    click.echo("-" * 65)
    for r in results:
        click.echo(f"{r.metric_a:<20} {r.metric_b:<20} {r.score:>7.2f} {r.co_occurrences:>7} {r.total_events:>7}")


@correlator.command("pair")
@click.argument("metric_a")
@click.argument("metric_b")
@click.option("--window", default=60.0, show_default=True)
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]), show_default=True)
def pair(metric_a: str, metric_b: str, window: float, fmt: str) -> None:
    """Show correlation between two specific metrics."""
    c = _build_sample_correlator()
    result = c.correlate(metric_a, metric_b, window_seconds=window)

    if result is None:
        click.echo(f"One or both metrics not found: {metric_a}, {metric_b}", err=True)
        raise SystemExit(1)

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
        return

    click.echo(f"Correlation: {metric_a} <-> {metric_b}")
    click.echo(f"  Score        : {result.score:.4f}")
    click.echo(f"  Co-occurrences: {result.co_occurrences}")
    click.echo(f"  Total events : {result.total_events}")
