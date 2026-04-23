import json
import click
from pipewatch.sla import SLAConfig, SLATracker
from pipewatch.history import MetricHistory
from pipewatch.metrics import MetricStatus, PipelineMetric, MetricEvaluation
from pipewatch.history import HistoryEntry
from datetime import datetime, timezone


def _build_sample_tracker() -> tuple[SLATracker, MetricHistory]:
    tracker = SLATracker()
    tracker.register(SLAConfig("orders", max_critical_ratio=0.05, max_warning_ratio=0.10))
    tracker.register(SLAConfig("payments", max_critical_ratio=0.02, max_warning_ratio=0.08))

    history = MetricHistory()
    statuses = [
        ("orders", MetricStatus.OK), ("orders", MetricStatus.OK),
        ("orders", MetricStatus.WARNING), ("orders", MetricStatus.CRITICAL),
        ("payments", MetricStatus.OK), ("payments", MetricStatus.OK),
        ("payments", MetricStatus.OK), ("payments", MetricStatus.WARNING),
    ]
    for name, status in statuses:
        metric = PipelineMetric(name=name, value=1.0)
        evaluation = MetricEvaluation(metric=metric, status=status)
        history.record(name, HistoryEntry(evaluation=evaluation, timestamp=datetime.now(timezone.utc)))
    return tracker, history


@click.group()
def sla():
    """SLA tracking commands."""


@sla.command("check")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]))
def check_sla(fmt: str):
    """Check SLA compliance for all registered metrics."""
    tracker, history = _build_sample_tracker()
    results = tracker.evaluate_all(history)

    if fmt == "json":
        click.echo(json.dumps({k: v.to_dict() for k, v in results.items()}, indent=2))
        return

    click.echo(f"{'Metric':<20} {'Crit%':>8} {'Warn%':>8} {'Crit Breach':>12} {'Warn Breach':>12}")
    click.echo("-" * 64)
    for name, result in results.items():
        crit_flag = "BREACHED" if result.critical_breached else "ok"
        warn_flag = "BREACHED" if result.warning_breached else "ok"
        click.echo(
            f"{name:<20} {result.critical_ratio * 100:>7.2f}% {result.warning_ratio * 100:>7.2f}%"
            f" {crit_flag:>12} {warn_flag:>12}"
        )


@sla.command("detail")
@click.argument("metric_name")
def detail(metric_name: str):
    """Show SLA detail for a specific metric."""
    tracker, history = _build_sample_tracker()
    result = tracker.evaluate(metric_name, history)
    if result is None:
        click.echo(f"No SLA config found for metric: {metric_name}", err=True)
        raise SystemExit(1)
    click.echo(json.dumps(result.to_dict(), indent=2))
