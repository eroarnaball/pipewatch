"""CLI extension for anomaly detection commands."""

import click
import json

from pipewatch.anomaly import AnomalyDetector
from pipewatch.history import MetricHistory
from pipewatch.history import HistoryEntry
from pipewatch.metrics import MetricStatus


def _build_sample_history(values):
    """Build a MetricHistory from a list of float values for CLI demo use."""
    history = MetricHistory(max_entries=200)
    for v in values:
        entry = HistoryEntry(value=v, status=MetricStatus.OK, timestamp=None)
        history._entries.append(entry)
    return history


@click.group()
def anomaly():
    """Anomaly detection commands."""
    pass


@anomaly.command("check")
@click.argument("metric_name")
@click.argument("value", type=float)
@click.option("--history", "history_values", multiple=True, type=float, help="Historical values for baseline.")
@click.option("--sensitivity", default=2.0, show_default=True, help="Z-score sensitivity threshold.")
@click.option("--min-samples", default=5, show_default=True, help="Minimum samples for baseline.")
@click.option("--json-output", is_flag=True, default=False, help="Output as JSON.")
def check_anomaly(metric_name, value, history_values, sensitivity, min_samples, json_output):
    """Check VALUE for METRIC_NAME against provided historical data."""
    detector = AnomalyDetector(sensitivity=sensitivity, min_samples=min_samples)
    history = _build_sample_history(list(history_values))

    metric_mock = type("M", (), {"name": metric_name})()
    ev_mock = type("E", (), {"value": value, "metric": metric_mock})()

    result = detector.evaluate(ev_mock, history)

    if result is None:
        click.echo("Insufficient data or missing value — cannot evaluate.")
        return

    if json_output:
        click.echo(json.dumps({
            "metric": metric_name,
            "value": value,
            "is_anomaly": result.is_anomaly,
            "z_score": result.z_score,
            "baseline": result.baseline.to_dict() if result.baseline else None,
        }, indent=2))
    else:
        status = click.style("ANOMALY", fg="red") if result.is_anomaly else click.style("OK", fg="green")
        click.echo(f"[{status}] {metric_name} = {value}  z={result.z_score}")
        if result.baseline:
            b = result.baseline
            click.echo(f"  baseline mean={b.mean:.4f} stddev={b.stddev:.4f} range=[{b.lower_bound:.4f}, {b.upper_bound:.4f}]")
