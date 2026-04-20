"""CLI commands for pipeline health scoring."""

import click
import json
from pipewatch.scorer import PipelineScorer
from pipewatch.metrics import PipelineMetric, MetricEvaluation, MetricStatus
from pipewatch.thresholds import ThresholdEvaluator


def _build_sample_evaluations():
    specs = [
        ("row_count", 1200, 500, 100),
        ("error_rate", 0.03, 0.05, 0.10),
        ("latency_ms", 320, 300, 500),
        ("null_ratio", 0.12, 0.10, 0.20),
    ]
    evaluations = []
    for name, value, warn, crit in specs:
        metric = PipelineMetric(name=name, value=value)
        evaluator = ThresholdEvaluator(warning=warn, critical=crit)
        ev = evaluator.evaluate(metric)
        evaluations.append(ev)
    return evaluations


@click.group()
def scorer():
    """Pipeline health scoring commands."""


@scorer.command("score")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
@click.option("--weight", "-w", multiple=True, help="metric:weight pairs, e.g. row_count:2.0")
def run_score(fmt, weight):
    """Compute and display the pipeline health score."""
    evaluations = _build_sample_evaluations()
    scorer_obj = PipelineScorer()

    for entry in weight:
        parts = entry.split(":")
        if len(parts) == 2:
            try:
                scorer_obj.set_weight(parts[0], float(parts[1]))
            except ValueError as exc:
                click.echo(f"Invalid weight '{entry}': {exc}", err=True)

    result = scorer_obj.score(evaluations)

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
        return

    click.echo(f"\nPipeline Health Score: {result.percentage:.1f}%  [Grade: {result.grade}]")
    click.echo(f"Score: {result.total_score:.2f} / {result.max_score:.2f}\n")
    click.echo(f"{'Metric':<20} {'Status':<12} {'Weight':>6} {'Score':>8}")
    click.echo("-" * 50)
    for ms in result.metric_scores:
        click.echo(f"{ms.name:<20} {ms.status.value:<12} {ms.weight:>6.1f} {ms.score:>8.4f}")


@scorer.command("grade")
def show_grade():
    """Show a one-line health grade for the pipeline."""
    evaluations = _build_sample_evaluations()
    result = PipelineScorer().score(evaluations)
    click.echo(f"Health grade: {result.grade} ({result.percentage:.1f}%)")
