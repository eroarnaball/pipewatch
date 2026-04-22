from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import List

import click

from pipewatch.heatmap import HeatmapBuilder
from pipewatch.history import MetricHistory, HistoryEntry
from pipewatch.metrics import MetricStatus


def _build_sample_builder() -> HeatmapBuilder:
    builder = HeatmapBuilder()
    base = datetime(2024, 1, 15, 0, 0, 0)
    statuses = [MetricStatus.OK, MetricStatus.WARNING, MetricStatus.CRITICAL, MetricStatus.OK]
    for name in ["pipeline.lag", "pipeline.errors"]:
        history = MetricHistory(max_entries=200)
        for i in range(48):
            ts = base + timedelta(hours=i)
            status = statuses[i % len(statuses)]
            entry = HistoryEntry(metric_name=name, value=float(i), status=status, timestamp=ts)
            history.record(entry)
        builder.register(name, history)
    return builder


@click.group()
def heatmap() -> None:
    """Heatmap commands for visualising metric status by hour-of-day."""


@heatmap.command("show")
@click.argument("metric")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
def show_heatmap(metric: str, fmt: str) -> None:
    """Show hourly status heatmap for a metric."""
    builder = _build_sample_builder()
    result = builder.build(metric)
    if result is None:
        click.echo(f"No data for metric: {metric}", err=True)
        raise SystemExit(1)

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
        return

    STATUS_SYMBOLS = {"ok": ".", "warning": "W", "critical": "!"}
    click.echo(f"Heatmap: {result.metric_name}")
    click.echo(f"{'Hour':>5}  {'Dom':>5}  Counts")
    click.echo("-" * 40)
    for cell in result.cells:
        sym = STATUS_SYMBOLS.get(cell.dominant_status(), "?")
        counts = "  ".join(f"{k}={v}" for k, v in cell.status_counts.items())
        click.echo(f"{cell.hour:>5}  {sym:>5}  {counts}")


@heatmap.command("all")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
def show_all(fmt: str) -> None:
    """Show heatmap summary for all registered metrics."""
    builder = _build_sample_builder()
    results = builder.build_all()
    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
        return
    for r in results:
        dominant_hours = [c.hour for c in r.cells if c.dominant_status() != "ok"]
        click.echo(f"{r.metric_name}: problem hours={dominant_hours}")
