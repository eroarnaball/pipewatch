"""CLI commands for metric fingerprint inspection."""

from __future__ import annotations

import json

import click

from pipewatch.metrics import MetricEvaluation, MetricStatus, PipelineMetric
from pipewatch.fingerprint import FingerprintRegistry


def _build_sample_registry() -> tuple[FingerprintRegistry, list[MetricEvaluation]]:
    registry = FingerprintRegistry()
    evaluations = [
        MetricEvaluation(
            metric=PipelineMetric(name="latency", value=120.0),
            status=MetricStatus.WARNING,
        ),
        MetricEvaluation(
            metric=PipelineMetric(name="error_rate", value=0.01),
            status=MetricStatus.OK,
        ),
        MetricEvaluation(
            metric=PipelineMetric(name="throughput", value=0.0),
            status=MetricStatus.CRITICAL,
        ),
    ]
    for ev in evaluations:
        registry.record(ev)
    return registry, evaluations


@click.group()
def fingerprint() -> None:
    """Inspect metric fingerprints."""


@fingerprint.command("list")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]))
def list_fingerprints(fmt: str) -> None:
    """List current fingerprints for all tracked metrics."""
    registry, evaluations = _build_sample_registry()
    fingerprints = [registry.compute(ev).to_dict() for ev in evaluations]

    if fmt == "json":
        click.echo(json.dumps(fingerprints, indent=2))
        return

    click.echo(f"{'METRIC':<20} {'STATUS':<12} {'VALUE':<10} {'FINGERPRINT'}")
    click.echo("-" * 60)
    for fp in fingerprints:
        click.echo(
            f"{fp['metric_name']:<20} {fp['status']:<12} "
            f"{str(fp['value']):<10} {fp['fingerprint']}"
        )


@fingerprint.command("changed")
@click.argument("metric_name")
def check_changed(metric_name: str) -> None:
    """Check whether a metric's fingerprint has changed since last record."""
    registry, evaluations = _build_sample_registry()
    match = next((ev for ev in evaluations if ev.metric.name == metric_name), None)
    if match is None:
        click.echo(f"Unknown metric: {metric_name}", err=True)
        raise SystemExit(1)

    # Simulate a change by bumping the value
    changed_ev = MetricEvaluation(
        metric=PipelineMetric(name=match.metric.name, value=(match.metric.value or 0) + 50),
        status=MetricStatus.CRITICAL,
    )
    changed = registry.has_changed(changed_ev)
    click.echo(f"{metric_name}: {'CHANGED' if changed else 'UNCHANGED'}")
