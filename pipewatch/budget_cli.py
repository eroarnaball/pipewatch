"""CLI commands for error budget inspection."""
import click
import json
from datetime import datetime, timedelta
from pipewatch.budget import BudgetConfig, ErrorBudgetTracker
from pipewatch.history import MetricHistory, HistoryEntry
from pipewatch.metrics import MetricStatus
from pipewatch.formatters import _colorize


def _build_sample_tracker() -> tuple:
    """Build a sample tracker and histories for demo purposes."""
    tracker = ErrorBudgetTracker()
    metrics = [
        ("latency", 0.10, 0.20),
        ("error_rate", 0.05, 0.15),
        ("throughput", 0.10, 0.25),
    ]
    histories = {}
    base = datetime(2024, 1, 1, 0, 0, 0)
    sample_statuses = {
        "latency": [MetricStatus.OK] * 7 + [MetricStatus.WARNING] * 2 + [MetricStatus.CRITICAL],
        "error_rate": [MetricStatus.CRITICAL] * 3 + [MetricStatus.OK] * 7,
        "throughput": [MetricStatus.OK] * 10,
    }
    for name, crit, warn in metrics:
        tracker.register(BudgetConfig(
            metric_name=name,
            window_size=10,
            allowed_critical_ratio=crit,
            allowed_warning_ratio=warn,
        ))
        h = MetricHistory(metric_name=name, max_entries=100)
        for i, status in enumerate(sample_statuses[name]):
            h.entries.append(HistoryEntry(
                timestamp=base + timedelta(minutes=i),
                value=float(i),
                status=status,
            ))
        histories[name] = h
    return tracker, histories


@click.group()
def budget():
    """Error budget tracking commands."""
    pass


@budget.command("check")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]),
              help="Output format.")
def check_budgets(fmt):
    """Check error budgets for all tracked metrics."""
    tracker, histories = _build_sample_tracker()
    results = []
    for name, history in histories.items():
        result = tracker.evaluate(name, history)
        if result:
            results.append(result)

    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
        return

    click.echo(f"{'Metric':<15} {'Window':>8} {'Crit%':>8} {'Warn%':>8} {'Budget OK':>12}")
    click.echo("-" * 55)
    for r in results:
        status_str = "EXCEEDED" if r.any_exceeded else "OK"
        color = "red" if r.any_exceeded else "green"
        click.echo(
            f"{r.metric_name:<15} {r.window_size:>8} "
            f"{r.critical_ratio*100:>7.1f}% {r.warning_ratio*100:>7.1f}% "
            f"{_colorize(status_str, color):>12}"
        )


@budget.command("detail")
@click.argument("metric_name")
def detail(metric_name):
    """Show detailed budget breakdown for a specific metric."""
    tracker, histories = _build_sample_tracker()
    history = histories.get(metric_name)
    if history is None:
        click.echo(f"No history found for metric: {metric_name}", err=True)
        raise SystemExit(1)
    result = tracker.evaluate(metric_name, history)
    if result is None:
        click.echo(f"No budget configured for metric: {metric_name}", err=True)
        raise SystemExit(1)
    click.echo(json.dumps(result.to_dict(), indent=2))
