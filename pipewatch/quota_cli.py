import click
import json
from datetime import datetime, timedelta
from pipewatch.quota import QuotaConfig, QuotaTracker
from pipewatch.history import MetricHistory, HistoryEntry
from pipewatch.metrics import MetricStatus


def _build_sample_tracker() -> tuple[QuotaTracker, MetricHistory]:
    tracker = QuotaTracker(default_config=QuotaConfig(max_warnings_pct=0.3, max_critical_pct=0.1))
    tracker.register("error_rate", QuotaConfig(max_warnings_pct=0.2, max_critical_pct=0.05))
    history = MetricHistory(max_entries=100)
    base = datetime.utcnow() - timedelta(hours=10)
    statuses = [
        MetricStatus.OK, MetricStatus.OK, MetricStatus.WARNING,
        MetricStatus.WARNING, MetricStatus.CRITICAL, MetricStatus.OK,
        MetricStatus.OK, MetricStatus.OK, MetricStatus.WARNING, MetricStatus.OK,
    ]
    for i, st in enumerate(statuses):
        entry = HistoryEntry(
            metric_name="error_rate",
            status=st,
            value=float(i),
            timestamp=base + timedelta(hours=i),
        )
        history.record(entry)
    return tracker, history


@click.group()
def quota():
    """Quota commands for pipeline metric health budgets."""


@quota.command("check")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]))
def check_quota(fmt: str):
    """Check quota usage for all registered metrics."""
    tracker, history = _build_sample_tracker()
    metrics = ["error_rate"]
    results = [tracker.evaluate(m, history) for m in metrics]
    results = [r for r in results if r is not None]

    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
        return

    click.echo(f"{'Metric':<20} {'Total':>6} {'Warn%':>8} {'Crit%':>8} {'Exceeded'}")
    click.echo("-" * 58)
    for r in results:
        exceeded = "YES" if r.any_exceeded else "no"
        click.echo(
            f"{r.metric_name:<20} {r.total:>6} "
            f"{r.warning_pct*100:>7.1f}% {r.critical_pct*100:>7.1f}% {exceeded}"
        )


@quota.command("detail")
@click.argument("metric_name")
def detail(metric_name: str):
    """Show detailed quota result for a specific metric."""
    tracker, history = _build_sample_tracker()
    result = tracker.evaluate(metric_name, history)
    if result is None:
        click.echo(f"No data found for metric: {metric_name}", err=True)
        raise SystemExit(1)
    click.echo(json.dumps(result.to_dict(), indent=2))
