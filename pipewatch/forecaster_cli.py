"""CLI commands for metric forecasting."""
from __future__ import annotations

import json
from datetime import datetime, timedelta

import click

from pipewatch.forecaster import MetricForecaster
from pipewatch.history import MetricHistory, HistoryEntry
from pipewatch.metrics import MetricStatus, PipelineMetric, MetricEvaluation


def _build_sample_history() -> MetricHistory:
    history = MetricHistory(max_entries=50)
    base = datetime(2024, 1, 1, 0, 0, 0)
    for i in range(25):
        metric = PipelineMetric(name="queue_depth", value=float(10 + i * 2))
        evaluation = MetricEvaluation(
            metric=metric,
            status=MetricStatus.OK if i < 20 else MetricStatus.WARNING,
        )
        entry = HistoryEntry(evaluation=evaluation, timestamp=base + timedelta(minutes=i * 5))
        history.record("queue_depth", entry)
    return history


@click.group()
def forecaster():
    """Metric forecasting commands."""


@forecaster.command("predict")
@click.argument("metric")
@click.option("--horizon", default=1, show_default=True, help="Steps ahead to forecast.")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]), show_default=True)
def predict(metric: str, horizon: int, fmt: str):
    """Forecast the next value for a metric."""
    history = _build_sample_history()
    forecaster_obj = MetricForecaster()
    result = forecaster_obj.forecast(history, metric, horizon=horizon)

    if result is None:
        click.echo(f"Not enough data to forecast '{metric}'.")
        raise SystemExit(1)

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        click.echo(f"Metric        : {result.metric_name}")
        click.echo(f"Horizon       : +{result.horizon} step(s)")
        click.echo(f"Predicted     : {result.predicted_value:.4f}")
        click.echo(f"Slope         : {result.slope:.6f}")
        click.echo(f"Confidence    : {result.confidence}")


@forecaster.command("multi")
@click.option("--horizon", default=3, show_default=True, help="Steps ahead.")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]), show_default=True)
def multi(horizon: int, fmt: str):
    """Forecast multiple horizons for the sample metric."""
    history = _build_sample_history()
    forecaster_obj = MetricForecaster()
    results = [
        forecaster_obj.forecast(history, "queue_depth", horizon=h)
        for h in range(1, horizon + 1)
    ]
    results = [r for r in results if r is not None]

    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        click.echo(f"{'Horizon':>8}  {'Predicted':>12}  {'Confidence':<10}")
        click.echo("-" * 36)
        for r in results:
            click.echo(f"{r.horizon:>8}  {r.predicted_value:>12.4f}  {r.confidence:<10}")
