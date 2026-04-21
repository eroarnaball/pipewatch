"""CLI commands for inspecting metric profiling data."""

from __future__ import annotations

import json
import random
import time

import click

from pipewatch.profiler import MetricProfiler


def _build_sample_profiler() -> MetricProfiler:
    profiler = MetricProfiler()
    rng = random.Random(42)
    metrics = ["row_count", "latency", "error_rate"]
    for metric in metrics:
        for _ in range(5):
            profiler.record(metric, round(rng.uniform(10.0, 300.0), 2))
    return profiler


@click.group()
def profiler() -> None:
    """Commands for viewing metric execution profiles."""


@profiler.command("list")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]))
def list_profiles(fmt: str) -> None:
    """List profiling summaries for all tracked metrics."""
    p = _build_sample_profiler()
    summaries = p.all_summaries()

    if fmt == "json":
        click.echo(json.dumps([s.to_dict() for s in summaries], indent=2))
        return

    header = f"{'METRIC':<20} {'COUNT':>6} {'MIN ms':>10} {'MAX ms':>10} {'AVG ms':>10}"
    click.echo(header)
    click.echo("-" * len(header))
    for s in summaries:
        click.echo(
            f"{s.metric_name:<20} {s.count:>6} {s.min_ms:>10.2f} {s.max_ms:>10.2f} {s.avg_ms:>10.2f}"
        )


@profiler.command("detail")
@click.argument("metric_name")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]))
def detail(metric_name: str, fmt: str) -> None:
    """Show individual profile entries for a specific metric."""
    p = _build_sample_profiler()
    entries = p.entries_for(metric_name)

    if not entries:
        click.echo(f"No profile data found for '{metric_name}'.")
        raise SystemExit(1)

    if fmt == "json":
        click.echo(json.dumps([e.to_dict() for e in entries], indent=2))
        return

    click.echo(f"Profile entries for '{metric_name}':")
    click.echo(f"  {'#':<4} {'DURATION ms':>12} {'TIMESTAMP':>20}")
    for i, e in enumerate(entries, 1):
        ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(e.timestamp))
        click.echo(f"  {i:<4} {e.duration_ms:>12.2f} {ts:>20}")
