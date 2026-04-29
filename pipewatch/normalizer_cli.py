"""CLI commands for the metric normalizer."""

import json
import click
from pipewatch.normalizer import MetricNormalizer


def _build_sample_normalizer() -> MetricNormalizer:
    n = MetricNormalizer()
    n.register("latency_ms", min_value=0.0, max_value=2000.0)
    n.register("error_rate", min_value=0.0, max_value=1.0)
    n.register("queue_depth", min_value=0.0, max_value=500.0)
    return n


@click.group()
def normalizer():
    """Normalize metric values to [0, 1] range."""


@normalizer.command("show")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
def show_bounds(fmt: str):
    """Show registered normalization bounds."""
    n = _build_sample_normalizer()
    bounds = n.all_bounds()

    if fmt == "json":
        click.echo(json.dumps({k: v.to_dict() for k, v in bounds.items()}, indent=2))
        return

    click.echo(f"{'Metric':<20} {'Min':>10} {'Max':>10}")
    click.echo("-" * 44)
    for name, b in bounds.items():
        click.echo(f"{name:<20} {b.min_value:>10.2f} {b.max_value:>10.2f}")


@normalizer.command("normalize")
@click.argument("metric")
@click.argument("value", type=float)
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
def normalize_value(metric: str, value: float, fmt: str):
    """Normalize a single VALUE for METRIC."""
    n = _build_sample_normalizer()
    result = n.normalize(metric, value)

    if result is None:
        click.echo(f"No bounds registered for metric: {metric}", err=True)
        raise SystemExit(1)

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
        return

    click.echo(f"Metric    : {result.metric_name}")
    click.echo(f"Raw value : {result.raw}")
    click.echo(f"Normalized: {result.normalized:.6f}")
    click.echo(f"Range     : [{result.bounds.min_value}, {result.bounds.max_value}]")
