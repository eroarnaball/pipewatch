"""CLI commands for inspecting the alert batcher state."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import click

from pipewatch.alerts import AlertMessage
from pipewatch.batcher import AlertBatcher


def _build_sample_batcher() -> AlertBatcher:
    batcher = AlertBatcher(window_seconds=30)
    base = datetime.utcnow() - timedelta(seconds=35)
    messages = [
        AlertMessage(metric_name="db.latency", status="critical", value=320.0, message="High latency"),
        AlertMessage(metric_name="queue.depth", status="warning", value=85.0, message="Queue growing"),
        AlertMessage(metric_name="cache.hit_rate", status="warning", value=0.61, message="Low hit rate"),
    ]
    for i, msg in enumerate(messages):
        batcher.enqueue(msg, now=base + timedelta(seconds=i * 2))
    return batcher


@click.group()
def batcher() -> None:
    """Manage alert batching windows."""


@batcher.command("status")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]))
def show_status(fmt: str) -> None:
    """Show current batcher queue status."""
    b = _build_sample_batcher()
    pending = b.pending_count()
    ready = b.is_ready()

    if fmt == "json":
        click.echo(json.dumps({"pending": pending, "ready": ready, "window_seconds": b._window_seconds}))
        return

    click.echo(f"{'Pending Alerts':<20} {'Window (s)':<14} {'Ready to Flush':<16}")
    click.echo("-" * 52)
    click.echo(f"{pending:<20} {b._window_seconds:<14} {str(ready):<16}")


@batcher.command("flush")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]))
def flush_batch(fmt: str) -> None:
    """Flush the current batch and display its contents."""
    b = _build_sample_batcher()
    batch = b.flush()

    if batch is None:
        click.echo("No alerts in queue.")
        return

    if fmt == "json":
        click.echo(json.dumps(batch.to_dict()))
        return

    click.echo(f"Flushed batch: {batch.size} alert(s) from window of {batch.window_seconds}s")
    click.echo(f"{'Metric':<25} {'Status':<12} {'Queued At'}")
    click.echo("-" * 60)
    for entry in batch.entries:
        click.echo(f"{entry.message.metric_name:<25} {entry.message.status:<12} {entry.queued_at.isoformat()}")
