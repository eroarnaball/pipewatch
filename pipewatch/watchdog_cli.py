"""CLI commands for watchdog staleness checks."""

import click
from datetime import datetime, timedelta
from pipewatch.watchdog import MetricWatchdog


def _build_sample_watchdog() -> MetricWatchdog:
    wd = MetricWatchdog(default_ttl=60)
    now = datetime.utcnow()
    metrics = {
        "orders.row_count": (now - timedelta(seconds=20), 60),
        "payments.latency": (now - timedelta(seconds=90), 60),
        "users.sync_lag": (now - timedelta(seconds=10), 120),
    }
    for name, (ts, ttl) in metrics.items():
        wd.register(name, ttl=ttl)
        wd.touch(name, at=ts)
    return wd


@click.group()
def watchdog():
    """Watchdog commands for staleness detection."""


@watchdog.command("check")
@click.option("--all", "show_all", is_flag=True, default=False, help="Show all metrics, not just stale.")
def check_staleness(show_all: bool):
    """Check for stale pipeline metrics."""
    wd = _build_sample_watchdog()
    now = datetime.utcnow()
    reports = wd.check_all(now=now) if show_all else wd.stale_metrics(now=now)

    if not reports:
        click.echo(click.style("All metrics are fresh.", fg="green"))
        return

    label = "All metrics" if show_all else "Stale metrics"
    click.echo(f"{label} ({len(reports)} found):")
    click.echo(f"  {'METRIC':<30} {'AGE (s)':>10} {'TTL (s)':>10} {'STATUS':>10}")
    click.echo("  " + "-" * 64)
    for r in reports:
        status = click.style("STALE", fg="red") if r.is_stale else click.style("OK", fg="green")
        click.echo(f"  {r.metric_name:<30} {r.age_seconds:>10.1f} {r.ttl_seconds:>10} {status:>10}")


@watchdog.command("status")
@click.argument("metric_name")
def metric_status(metric_name: str):
    """Show staleness status for a specific metric."""
    wd = _build_sample_watchdog()
    report = wd.check(metric_name)
    if report is None:
        click.echo(click.style(f"Metric '{metric_name}' not found or never recorded.", fg="yellow"))
        return
    color = "red" if report.is_stale else "green"
    click.echo(click.style(f"{'STALE' if report.is_stale else 'FRESH'}: {metric_name}", fg=color))
    click.echo(f"  Last seen : {report.last_seen.isoformat()}")
    click.echo(f"  Age       : {report.age_seconds:.1f}s")
    click.echo(f"  TTL       : {report.ttl_seconds}s")
