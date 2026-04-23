"""CLI commands for inspecting the alert stagger queue."""

from __future__ import annotations

import json
import time

import click

from pipewatch.stagger import AlertStagger
from pipewatch.alerts import AlertMessage
from pipewatch.metrics import MetricStatus


def _build_sample_stagger() -> AlertStagger:
    stagger = AlertStagger(interval_seconds=3.0)
    now = time.time()
    for name, status in [
        ("pipeline.lag", MetricStatus.WARNING),
        ("pipeline.errors", MetricStatus.CRITICAL),
        ("pipeline.throughput", MetricStatus.WARNING),
    ]:
        msg = AlertMessage(
            metric_name=name,
            status=status,
            value=42.0,
            message=f"{name} is {status.value}",
        )
        stagger.enqueue(msg)
    return stagger


@click.group()
def stagger() -> None:
    """Staggered alert queue commands."""


@stagger.command("queue")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]))
def show_queue(fmt: str) -> None:
    """Show pending alerts in the stagger queue."""
    s = _build_sample_stagger()
    pending = s.pending()

    if fmt == "json":
        click.echo(json.dumps([a.to_dict() for a in pending], indent=2))
        return

    click.echo(f"{'Metric':<30} {'Status':<10} {'Scheduled At':<20} {'Sent':<6}")
    click.echo("-" * 70)
    for a in pending:
        ts = time.strftime("%H:%M:%S", time.localtime(a.scheduled_at))
        click.echo(f"{a.message.metric_name:<30} {a.message.status.value:<10} {ts:<20} {str(a.sent):<6}")


@stagger.command("flush")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]))
def flush_queue(fmt: str) -> None:
    """Flush all currently-due alerts from the queue."""
    s = _build_sample_stagger()
    flushed = s.flush(now=time.time() + 100)

    if fmt == "json":
        click.echo(json.dumps([a.to_dict() for a in flushed], indent=2))
        return

    click.echo(f"Flushed {len(flushed)} alert(s).")
    for a in flushed:
        click.echo(f"  - {a.message.metric_name} [{a.message.status.value}]")
