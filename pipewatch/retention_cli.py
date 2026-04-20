"""CLI commands for inspecting and running retention policies."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import click

from pipewatch.history import MetricHistory, HistoryEntry
from pipewatch.metrics import MetricStatus, PipelineMetric, MetricEvaluation
from pipewatch.retention import RetentionPolicy, RetentionManager


def _build_sample_data() -> dict:
    """Build sample histories for demo purposes."""
    now = datetime.utcnow()

    def _make_entry(seconds_ago: int, value: float) -> HistoryEntry:
        metric = PipelineMetric(name="demo", value=value, unit="ms")
        ev = MetricEvaluation(
            metric=metric,
            status=MetricStatus.OK,
            message="ok",
        )
        entry = HistoryEntry(evaluation=ev)
        entry.timestamp = now - timedelta(seconds=seconds_ago)
        return entry

    hist = MetricHistory(max_entries=500)
    hist.entries = [
        _make_entry(100, 1.0),
        _make_entry(3600, 2.0),
        _make_entry(90000, 3.0),  # older than 24 h
    ]
    return {"demo": hist}


@click.group()
def retention() -> None:
    """Manage metric history retention."""


@retention.command("run")
@click.option("--ttl", default=86400, show_default=True, help="Default TTL in seconds.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def run_retention(ttl: int, as_json: bool) -> None:
    """Prune history entries that exceed the TTL."""
    policy = RetentionPolicy(default_ttl_seconds=ttl)
    manager = RetentionManager(policy)
    histories = _build_sample_data()
    results = manager.prune_all(histories)

    if as_json:
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
        return

    for r in results:
        click.echo(
            f"{r.metric_name}: removed {r.removed} entr"
            f"{'y' if r.removed == 1 else 'ies'}, {r.remaining} remaining"
        )


@retention.command("policy")
@click.option("--ttl", default=86400, show_default=True, help="Default TTL in seconds.")
def show_policy(ttl: int) -> None:
    """Display the active retention policy."""
    policy = RetentionPolicy(default_ttl_seconds=ttl)
    click.echo(json.dumps(policy.to_dict(), indent=2))
