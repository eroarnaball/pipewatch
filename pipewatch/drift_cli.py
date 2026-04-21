"""CLI commands for metric drift detection."""

import json
import click
from datetime import datetime, timezone
from pipewatch.drift import MetricDriftDetector
from pipewatch.history import MetricHistory, HistoryEntry
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.thresholds import ThresholdEvaluator


def _build_sample_history(name: str, values: list) -> MetricHistory:
    hist = MetricHistory(max_entries=50)
    evaluator = ThresholdEvaluator(warning=50.0, critical=80.0)
    for v in values:
        metric = PipelineMetric(name=name, value=v)
        evaluation = evaluator.evaluate(metric)
        entry = HistoryEntry(evaluation=evaluation, recorded_at=datetime.now(timezone.utc))
        hist.record(evaluation)
    return hist


@click.group()
def drift():
    """Detect value drift in pipeline metrics."""


@drift.command("check")
@click.option("--metric", default="latency", show_default=True, help="Metric name to inspect.")
@click.option("--threshold", default=20.0, show_default=True, help="Drift threshold percentage.")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]), show_default=True)
def check_drift(metric: str, threshold: float, fmt: str):
    """Check whether a metric has drifted from its baseline."""
    baseline = list(range(10, 20))          # stable baseline: 10..19
    recent = [v + 25 for v in range(3)]    # shifted recent values
    history = _build_sample_history(metric, baseline + recent)

    detector = MetricDriftDetector(baseline_size=10, recent_size=3, threshold_pct=threshold)
    result = detector.detect(metric, history)

    if result is None:
        click.echo("Insufficient data to detect drift.")
        return

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        status = click.style("DRIFTING", fg="red") if result.is_drifting else click.style("STABLE", fg="green")
        click.echo(f"Metric       : {result.metric_name}")
        click.echo(f"Baseline avg : {result.baseline_avg:.4f}")
        click.echo(f"Recent avg   : {result.recent_avg:.4f}")
        click.echo(f"Drift abs    : {result.drift_absolute:+.4f}")
        click.echo(f"Drift pct    : {result.drift_percent:.2f}%")
        click.echo(f"Status       : {status}")
