import click
import json
from datetime import datetime, timedelta
from pipewatch.ratelimiter import AlertRateLimiter


def _build_sample_limiter() -> AlertRateLimiter:
    limiter = AlertRateLimiter(default_max=3, default_window=60)
    limiter.configure("row_count", max_alerts=2, window_seconds=120)
    limiter.configure("latency_p99", max_alerts=5, window_seconds=300)
    now = datetime.utcnow()
    limiter.allow("row_count", now=now - timedelta(seconds=30))
    limiter.allow("row_count", now=now - timedelta(seconds=10))
    limiter.allow("latency_p99", now=now - timedelta(seconds=20))
    return limiter


@click.group()
def ratelimiter():
    """Manage alert rate limiting per metric."""


@ratelimiter.command("status")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]))
def show_status(fmt: str):
    """Show current rate limit status for all metrics."""
    limiter = _build_sample_limiter()
    statuses = limiter.all_statuses()

    if fmt == "json":
        click.echo(json.dumps(statuses, indent=2))
        return

    if not statuses:
        click.echo("No rate limit entries found.")
        return

    click.echo(f"{'Metric':<20} {'Max':>5} {'Window(s)':>10} {'Count':>6} {'Remaining':>10} {'Limited':>8}")
    click.echo("-" * 65)
    for s in statuses:
        limited_str = click.style("YES", fg="red") if s["is_limited"] else click.style("no", fg="green")
        click.echo(
            f"{s['metric_name']:<20} {s['max_alerts']:>5} {s['window_seconds']:>10} "
            f"{s['current_count']:>6} {s['remaining']:>10} {limited_str:>8}"
        )


@ratelimiter.command("reset")
@click.argument("metric_name")
def reset_metric(metric_name: str):
    """Reset the rate limit counter for a metric."""
    limiter = _build_sample_limiter()
    if limiter.reset(metric_name):
        click.echo(f"Rate limit counter reset for '{metric_name}'.")
    else:
        click.echo(f"No rate limit entry found for '{metric_name}'.", err=True)
        raise SystemExit(1)
