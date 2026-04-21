import click
import json
from datetime import datetime, timedelta
from pipewatch.notifier import NotificationThrottle
from pipewatch.metrics import MetricStatus


def _build_sample_throttle() -> NotificationThrottle:
    throttle = NotificationThrottle(cooldown_seconds=60)
    return throttle


@click.group()
def throttle():
    """Manage and inspect notification throttle state."""
    pass


@throttle.command("status")
@click.option("--metric", multiple=True, default=["pipeline.latency", "pipeline.errors", "pipeline.throughput"], help="Metric names to inspect")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]), help="Output format")
def show_status(metric, fmt):
    """Show current throttle state for metrics."""
    th = _build_sample_throttle()

    # Simulate some state
    th.should_notify("pipeline.latency", MetricStatus.WARNING)
    th.should_notify("pipeline.errors", MetricStatus.CRITICAL)

    rows = []
    for name in metric:
        state = th._states.get(name)
        if state:
            rows.append({
                "metric": name,
                "last_status": state.last_status.value if state.last_status else "none",
                "last_notified": state.last_notified.isoformat() if state.last_notified else "never",
                "suppressed": not th.should_notify(name, state.last_status) if state.last_status else False,
            })
        else:
            rows.append({
                "metric": name,
                "last_status": "none",
                "last_notified": "never",
                "suppressed": False,
            })

    if fmt == "json":
        click.echo(json.dumps(rows, indent=2))
    else:
        click.echo(f"{'Metric':<30} {'Last Status':<14} {'Last Notified':<26} {'Suppressed'}")
        click.echo("-" * 85)
        for r in rows:
            click.echo(f"{r['metric']:<30} {r['last_status']:<14} {r['last_notified']:<26} {r['suppressed']}")


@throttle.command("reset")
@click.argument("metric_name")
def reset_metric(metric_name):
    """Reset throttle state for a specific metric."""
    th = _build_sample_throttle()
    th.reset(metric_name)
    click.echo(f"Throttle state reset for metric: {metric_name}")
