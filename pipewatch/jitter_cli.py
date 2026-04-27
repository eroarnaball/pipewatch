"""CLI commands for inspecting alert jitter scheduling."""

from __future__ import annotations

import json
from datetime import datetime

import click

from pipewatch.alerts import AlertMessage
from pipewatch.jitter import AlertJitter
from pipewatch.metrics import MetricStatus


def _build_sample_jitter(seed: int = 42) -> tuple[AlertJitter, list[AlertMessage]]:
    jitter = AlertJitter(max_jitter_seconds=60.0)
    jitter.seed(seed)
    messages = [
        AlertMessage(metric_name="pipeline.lag", status=MetricStatus.WARNING, value=120.0, threshold=100.0),
        AlertMessage(metric_name="pipeline.errors", status=MetricStatus.CRITICAL, value=55.0, threshold=50.0),
        AlertMessage(metric_name="pipeline.throughput", status=MetricStatus.WARNING, value=80.0, threshold=75.0),
    ]
    return jitter, messages


@click.group()
def jitter() -> None:
    """Inspect alert jitter scheduling."""


@jitter.command("schedule")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]), show_default=True)
@click.option("--max-jitter", default=60.0, type=float, show_default=True, help="Max jitter in seconds.")
def show_schedule(fmt: str, max_jitter: float) -> None:
    """Show jittered schedule for sample alerts."""
    j, messages = _build_sample_jitter()
    j.max_jitter_seconds = max_jitter
    base = datetime(2024, 1, 1, 12, 0, 0)
    alerts = j.schedule_batch(messages, base_time=base)

    if fmt == "json":
        click.echo(json.dumps([a.to_dict() for a in alerts], indent=2))
        return

    header = f"{'Metric':<30} {'Status':<10} {'Jitter (s)':>12} {'Scheduled At'}"
    click.echo(header)
    click.echo("-" * len(header))
    for alert in alerts:
        click.echo(
            f"{alert.message.metric_name:<30} {alert.message.status:<10} "
            f"{alert.jitter_seconds:>12.3f} {alert.scheduled_at.isoformat()}"
        )
