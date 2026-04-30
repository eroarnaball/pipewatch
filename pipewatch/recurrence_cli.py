import json
from typing import List

import click

from pipewatch.metrics import MetricStatus
from pipewatch.recurrence import RecurrenceTracker


def _build_sample_tracker() -> RecurrenceTracker:
    tracker = RecurrenceTracker(threshold=3)
    statuses = [
        ("orders.lag", MetricStatus.WARNING),
        ("orders.lag", MetricStatus.WARNING),
        ("orders.lag", MetricStatus.WARNING),
        ("orders.lag", MetricStatus.WARNING),
        ("payments.error_rate", MetricStatus.CRITICAL),
        ("payments.error_rate", MetricStatus.CRITICAL),
        ("queue.depth", MetricStatus.WARNING),
    ]
    for name, status in statuses:
        tracker.record(name, status)
    return tracker


@click.group()
def recurrence() -> None:
    """Commands for recurring alert detection."""


@recurrence.command("show")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]))
def show_recurring(fmt: str) -> None:
    """Show all metrics currently flagged as recurring."""
    tracker = _build_sample_tracker()
    entries = tracker.all_recurring()

    if fmt == "json":
        click.echo(json.dumps([e.to_dict() for e in entries], indent=2))
        return

    if not entries:
        click.echo("No recurring alerts detected.")
        return

    click.echo(f"{'Metric':<30} {'Status':<10} {'Count':>6} {'First Seen':<25} {'Last Seen':<25}")
    click.echo("-" * 100)
    for e in entries:
        click.echo(
            f"{e.metric_name:<30} {e.status.value:<10} {e.count:>6} "
            f"{e.first_seen.isoformat():<25} {e.last_seen.isoformat():<25}"
        )


@recurrence.command("check")
@click.argument("metric_name")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]))
def check_metric(metric_name: str, fmt: str) -> None:
    """Check recurrence status for a specific metric."""
    tracker = _build_sample_tracker()
    entry = tracker.get_entry(metric_name)

    if entry is None:
        click.echo(f"No recurrence data for '{metric_name}'.")
        raise SystemExit(1)

    result = {
        "metric_name": entry.metric_name,
        "status": entry.status.value,
        "count": entry.count,
        "is_recurring": entry.count >= tracker.threshold,
        "first_seen": entry.first_seen.isoformat(),
        "last_seen": entry.last_seen.isoformat(),
    }

    if fmt == "json":
        click.echo(json.dumps(result, indent=2))
        return

    click.echo(f"Metric:      {entry.metric_name}")
    click.echo(f"Status:      {entry.status.value}")
    click.echo(f"Count:       {entry.count}")
    click.echo(f"Recurring:   {result['is_recurring']}")
    click.echo(f"First seen:  {entry.first_seen.isoformat()}")
    click.echo(f"Last seen:   {entry.last_seen.isoformat()}")
