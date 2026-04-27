"""CLI commands for cascade failure detection."""

import json
import click
from pipewatch.cascade import CascadeDetector
from pipewatch.metrics import MetricStatus, PipelineMetric, MetricEvaluation


def _build_sample_detector() -> tuple[CascadeDetector, list[MetricEvaluation]]:
    detector = CascadeDetector()
    detector.register_dependency("transform", "ingest")
    detector.register_dependency("load", "transform")
    detector.register_dependency("report", "load")

    def _ev(name: str, status: MetricStatus, value: float) -> MetricEvaluation:
        m = PipelineMetric(name=name, value=value, unit="count")
        return MetricEvaluation(metric=m, status=status, message=f"{name} is {status.value}")

    evaluations = [
        _ev("ingest", MetricStatus.CRITICAL, 0.0),
        _ev("transform", MetricStatus.CRITICAL, 0.0),
        _ev("load", MetricStatus.WARNING, 1.0),
        _ev("report", MetricStatus.OK, 5.0),
    ]
    return detector, evaluations


@click.group()
def cascade():
    """Cascade failure detection commands."""


@cascade.command("check")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
def check_cascade(fmt: str) -> None:
    """Detect cascade failures in sample pipeline metrics."""
    detector, evaluations = _build_sample_detector()
    result = detector.detect(evaluations)

    if result is None:
        click.echo("No cascade failures detected.")
        return

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
        return

    click.echo(f"Root cause : {result.root_cause}")
    click.echo(f"Cascade    : {'Yes' if result.is_cascade() else 'No'}")
    click.echo(f"Depth      : {result.depth}")
    click.echo("")
    click.echo(f"{'Metric':<20} {'Status':<12} {'Triggered By'}")
    click.echo("-" * 50)
    for node in result.affected:
        triggered = node.triggered_by or "-"
        click.echo(f"{node.metric_name:<20} {node.status.value:<12} {triggered}")


@cascade.command("root")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
def show_root(fmt: str) -> None:
    """Show only the root cause of any detected cascade."""
    detector, evaluations = _build_sample_detector()
    result = detector.detect(evaluations)

    if result is None:
        click.echo("No cascade detected.")
        return

    if fmt == "json":
        click.echo(json.dumps({"root_cause": result.root_cause, "depth": result.depth}))
        return

    click.echo(f"Root cause: {result.root_cause} (cascade depth: {result.depth})")
