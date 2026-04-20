"""CLI commands for metric enrichment inspection."""

import json
import click

from pipewatch.metrics import MetricStatus, PipelineMetric, MetricEvaluation
from pipewatch.enricher import MetricEnricher


def _build_sample_enricher() -> MetricEnricher:
    enricher = MetricEnricher()
    enricher.register("is_critical", lambda ev: ev.status == MetricStatus.CRITICAL)
    enricher.register("label", lambda ev: ev.metric.name.upper())
    enricher.register(
        "severity_score",
        lambda ev: {MetricStatus.OK: 0, MetricStatus.WARNING: 1, MetricStatus.CRITICAL: 2}.get(
            ev.status, -1
        ),
    )
    return enricher


def _build_sample_evaluations():
    metrics = [
        ("row_count", 1200.0, MetricStatus.OK),
        ("error_rate", 0.15, MetricStatus.WARNING),
        ("latency_p99", 9.8, MetricStatus.CRITICAL),
    ]
    results = []
    for name, value, status in metrics:
        m = PipelineMetric(name=name, value=value, unit="")
        results.append(MetricEvaluation(metric=m, status=status))
    return results


@click.group()
def enricher():
    """Inspect enriched metric evaluations."""


@enricher.command("list")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]))
def list_enriched(fmt):
    """List all evaluations with enrichment metadata."""
    e = _build_sample_enricher()
    evaluations = _build_sample_evaluations()
    enriched = e.enrich_all(evaluations)

    if fmt == "json":
        click.echo(json.dumps([ev.to_dict() for ev in enriched], indent=2))
        return

    click.echo(f"{'Metric':<20} {'Status':<10} {'Critical':<10} {'Score':<8} Label")
    click.echo("-" * 60)
    for ev in enriched:
        click.echo(
            f"{ev.evaluation.metric.name:<20} "
            f"{ev.evaluation.status.value:<10} "
            f"{str(ev.get('is_critical')):<10} "
            f"{ev.get('severity_score'):<8} "
            f"{ev.get('label')}"
        )
