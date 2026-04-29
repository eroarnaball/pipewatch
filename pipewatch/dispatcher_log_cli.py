"""CLI commands for inspecting the dispatcher alert log."""

import json
from datetime import datetime

import click

from pipewatch.dispatcher_log import DispatchRecord, DispatcherLog
from pipewatch.metrics import MetricStatus


def _build_sample_log() -> DispatcherLog:
    log = DispatcherLog()
    samples = [
        ("orders.lag", MetricStatus.CRITICAL, "console", "orders.lag is CRITICAL", True, None),
        ("orders.lag", MetricStatus.WARNING, "slack", "orders.lag is WARNING", True, None),
        ("payments.errors", MetricStatus.CRITICAL, "pagerduty", "payments.errors is CRITICAL", False, "timeout"),
        ("inventory.count", MetricStatus.OK, "console", "inventory.count is OK", True, None),
    ]
    for name, status, channel, msg, success, error in samples:
        log.record(
            DispatchRecord(
                metric_name=name,
                status=status,
                channel=channel,
                message=msg,
                dispatched_at=datetime.utcnow(),
                success=success,
                error=error,
            )
        )
    return log


@click.group()
def dispatcher_log() -> None:
    """Inspect the alert dispatcher log."""


@dispatcher_log.command("list")
@click.option("--metric", default=None, help="Filter by metric name.")
@click.option("--channel", default=None, help="Filter by channel name.")
@click.option("--failures-only", is_flag=True, default=False, help="Show only failed dispatches.")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]), show_default=True)
def list_records(metric: str, channel: str, failures_only: bool, fmt: str) -> None:
    """List dispatched alert records."""
    log = _build_sample_log()
    records = log.failures() if failures_only else log.all()
    if metric:
        records = [r for r in records if r.metric_name == metric]
    if channel:
        records = [r for r in records if r.channel == channel]

    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in records], indent=2))
        return

    click.echo(f"{'METRIC':<25} {'STATUS':<10} {'CHANNEL':<12} {'OK':<5} {'ERROR'}")
    click.echo("-" * 70)
    for r in records:
        ok_str = "yes" if r.success else "no"
        err_str = r.error or ""
        click.echo(f"{r.metric_name:<25} {r.status.value:<10} {r.channel:<12} {ok_str:<5} {err_str}")
    click.echo(f"\nTotal: {len(records)}")


@dispatcher_log.command("summary")
def summary() -> None:
    """Show summary counts for the dispatcher log."""
    log = _build_sample_log()
    records = log.all()
    failures = log.failures()
    critical = log.by_status(MetricStatus.CRITICAL)
    warning = log.by_status(MetricStatus.WARNING)
    click.echo(f"Total dispatched : {len(records)}")
    click.echo(f"Failures         : {len(failures)}")
    click.echo(f"Critical alerts  : {len(critical)}")
    click.echo(f"Warning alerts   : {len(warning)}")
