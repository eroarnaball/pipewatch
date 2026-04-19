"""CLI entry-point for pipewatch."""
import json
import sys

import click

from pipewatch.collector import MetricCollector
from pipewatch.metrics import MetricStatus
from pipewatch.thresholds import ThresholdEvaluator


@click.group()
def cli():
    """pipewatch — monitor and alert on data pipeline health metrics."""


@cli.command("check")
@click.option("--pipeline", required=True, help="Pipeline name to report on.")
@click.option("--metric", required=True, help="Metric name.")
@click.option("--value", required=True, type=float, help="Current metric value.")
@click.option("--warning", default=None, type=float, help="Warning threshold.")
@click.option("--critical", default=None, type=float, help="Critical threshold.")
@click.option("--comparator", default="gte", type=click.Choice(["gte", "lte"]), show_default=True)
@click.option("--unit", default=None, help="Unit label (e.g. seconds, rows).")
@click.option("--output", default="text", type=click.Choice(["text", "json"]), show_default=True)
def check(pipeline, metric, value, warning, critical, comparator, unit, output):
    """Evaluate a single metric value against thresholds."""
    from pipewatch.metrics import PipelineMetric

    m = PipelineMetric(pipeline_name=pipeline, metric_name=metric, value=value, unit=unit)
    evaluator = ThresholdEvaluator(warning=warning, critical=critical, comparator=comparator)
    result = evaluator.evaluate(m)

    if output == "json":
        click.echo(json.dumps({"status": result.status.value, "message": result.message, **m.to_dict()}))
    else:
        color = {MetricStatus.OK: "green", MetricStatus.WARNING: "yellow", MetricStatus.CRITICAL: "red"}.get(
            result.status, "white"
        )
        click.echo(click.style(f"[{result.status.value.upper()}] {result.message}", fg=color))

    if result.status == MetricStatus.CRITICAL:
        sys.exit(2)
    elif result.status == MetricStatus.WARNING:
        sys.exit(1)


if __name__ == "__main__":
    cli()
