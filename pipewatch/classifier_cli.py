"""CLI commands for metric classification."""
from __future__ import annotations
import json
import click
from pipewatch.classifier import ClassificationRule, MetricClassifier
from pipewatch.metrics import MetricStatus, PipelineMetric, MetricEvaluation


def _build_sample_classifier() -> tuple[MetricClassifier, list[MetricEvaluation]]:
    classifier = MetricClassifier()
    classifier.add_rule(ClassificationRule("low-warning", MetricStatus.WARNING, min_value=0.0, max_value=50.0))
    classifier.add_rule(ClassificationRule("high-warning", MetricStatus.WARNING, min_value=50.0))
    classifier.add_rule(ClassificationRule("critical", MetricStatus.CRITICAL))

    evaluations = [
        MetricEvaluation(metric=PipelineMetric(name="latency", value=30.0), status=MetricStatus.WARNING),
        MetricEvaluation(metric=PipelineMetric(name="error_rate", value=75.0), status=MetricStatus.WARNING),
        MetricEvaluation(metric=PipelineMetric(name="throughput", value=5.0), status=MetricStatus.CRITICAL),
        MetricEvaluation(metric=PipelineMetric(name="queue_depth", value=10.0), status=MetricStatus.OK),
    ]
    return classifier, evaluations


@click.group()
def classifier():
    """Metric classification commands."""


@classifier.command("list")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
def list_classifications(fmt: str) -> None:
    """Classify all sample metrics and display results."""
    clf, evaluations = _build_sample_classifier()
    results = clf.classify_all(evaluations)

    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
        return

    click.echo(f"{'METRIC':<20} {'STATUS':<12} {'CLASS':<20} {'VALUE':>8}")
    click.echo("-" * 64)
    for r in results:
        cls_label = r.matched_class or "(unclassified)"
        click.echo(f"{r.metric_name:<20} {r.status.value:<12} {cls_label:<20} {r.value:>8.2f}")


@classifier.command("rules")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
def list_rules(fmt: str) -> None:
    """List all configured classification rules."""
    clf, _ = _build_sample_classifier()
    rules = clf.rules()

    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in rules], indent=2))
        return

    click.echo(f"{'RULE':<20} {'STATUS':<12} {'MIN':>10} {'MAX':>10}")
    click.echo("-" * 56)
    for r in rules:
        mn = f"{r.min_value:.1f}" if r.min_value is not None else "—"
        mx = f"{r.max_value:.1f}" if r.max_value is not None else "—"
        click.echo(f"{r.name:<20} {r.status.value:<12} {mn:>10} {mx:>10}")
