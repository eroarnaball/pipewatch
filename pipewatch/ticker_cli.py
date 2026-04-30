"""CLI commands for inspecting metric tick intervals."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta

import click

from pipewatch.ticker import MetricTicker


def _build_sample_ticker() -> MetricTicker:
    ticker = MetricTicker()
    base = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    for i in range(5):
        ticker.tick("orders.latency", at=base + timedelta(seconds=i * 30))
    for i in range(3):
        ticker.tick("queue.depth", at=base + timedelta(seconds=i * 60))
    return ticker


@click.group()
def ticker() -> None:
    """Inspect metric tick intervals and cadence."""


@ticker.command("stats")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]))
def show_stats(fmt: str) -> None:
    """Show tick statistics for all metrics."""
    t = _build_sample_ticker()
    all_stats = t.all_stats()
    if fmt == "json":
        click.echo(json.dumps([s.to_dict() for s in all_stats], indent=2))
        return
    click.echo(f"{'Metric':<25} {'Ticks':>6} {'Avg(s)':>9} {'Min(s)':>9} {'Max(s)':>9}")
    click.echo("-" * 62)
    for s in all_stats:
        avg = f"{s.avg_interval_seconds:.1f}" if s.avg_interval_seconds is not None else "N/A"
        mn = f"{s.min_interval_seconds:.1f}" if s.min_interval_seconds is not None else "N/A"
        mx = f"{s.max_interval_seconds:.1f}" if s.max_interval_seconds is not None else "N/A"
        click.echo(f"{s.metric_name:<25} {s.tick_count:>6} {avg:>9} {mn:>9} {mx:>9}")


@ticker.command("detail")
@click.argument("metric_name")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]))
def show_detail(metric_name: str, fmt: str) -> None:
    """Show individual tick entries for a metric."""
    t = _build_sample_ticker()
    entries = t.entries_for(metric_name)
    if not entries:
        click.echo(f"No tick data for '{metric_name}'.")
        raise SystemExit(1)
    if fmt == "json":
        click.echo(json.dumps([e.to_dict() for e in entries], indent=2))
        return
    click.echo(f"Tick history for '{metric_name}':")
    click.echo(f"  {'#':<4} {'Ticked At':<30} {'Interval(s)':>12}")
    click.echo("  " + "-" * 48)
    for i, e in enumerate(entries, 1):
        iv = f"{e.interval_seconds:.1f}" if e.interval_seconds is not None else "first"
        click.echo(f"  {i:<4} {e.ticked_at.isoformat():<30} {iv:>12}")
