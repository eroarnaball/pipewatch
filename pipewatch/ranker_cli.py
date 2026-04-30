"""CLI commands for the metric ranker."""

import json
import click
from pipewatch.ranker import MetricRanker
from pipewatch.metrics import MetricEvaluation, MetricStatus, PipelineMetric


def _build_sample_evaluations() -> list:
    def _ev(name: str, status: MetricStatus, value: float) -> MetricEvaluation:
        metric = PipelineMetric(name=name, value=value)
        return MetricEvaluation(metric=metric, status=status)

    return [
        _ev("db.query_time", MetricStatus.CRITICAL, 9.8),
        _ev("cache.hit_rate", MetricStatus.OK, 0.3),
        _ev("queue.depth", MetricStatus.WARNING, 4.2),
        _ev("api.latency", MetricStatus.WARNING, 1.1),
        _ev("disk.usage", MetricStatus.CRITICAL, 7.5),
        _ev("cpu.load", MetricStatus.OK, 0.6),
    ]


@click.group()
def ranker():
    """Metric ranking commands."""
    pass


@ranker.command("top")
@click.option("--n", default=5, show_default=True, help="Number of top metrics to show.")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]), show_default=True)
@click.option("--status-weight", default=0.7, type=float, show_default=True)
@click.option("--value-weight", default=0.3, type=float, show_default=True)
def show_top(n, fmt, status_weight, value_weight):
    """Show the top-N ranked metrics by severity."""
    try:
        r = MetricRanker(value_weight=value_weight, status_weight=status_weight)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)

    evaluations = _build_sample_evaluations()
    ranked = r.top(evaluations, n=n)

    if fmt == "json":
        click.echo(json.dumps([m.to_dict() for m in ranked], indent=2))
    else:
        click.echo(f"{'Rank':<6} {'Metric':<24} {'Status':<10} {'Value':>8} {'Score':>8}")
        click.echo("-" * 60)
        for m in ranked:
            click.echo(f"{m.rank:<6} {m.name:<24} {m.status.value:<10} {m.value:>8.2f} {m.score:>8.4f}")


@ranker.command("all")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]), show_default=True)
def show_all(fmt):
    """Show all metrics ranked by severity."""
    r = MetricRanker()
    evaluations = _build_sample_evaluations()
    ranked = r.rank(evaluations)

    if fmt == "json":
        click.echo(json.dumps([m.to_dict() for m in ranked], indent=2))
    else:
        click.echo(f"{'Rank':<6} {'Metric':<24} {'Status':<10} {'Value':>8} {'Score':>8}")
        click.echo("-" * 60)
        for m in ranked:
            click.echo(f"{m.rank:<6} {m.name:<24} {m.status.value:<10} {m.value:>8.2f} {m.score:>8.4f}")
