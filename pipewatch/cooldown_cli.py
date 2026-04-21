"""CLI commands for inspecting alert cooldown state."""

import json
from datetime import datetime, timedelta

import click

from pipewatch.cooldown import AlertCooldown
from pipewatch.formatters import _colorize


def _build_sample_cooldown() -> AlertCooldown:
    cd = AlertCooldown(default_seconds=300)
    cd.set_override("db_latency", 60)
    now = datetime.utcnow()
    cd.trigger("db_latency", now=now - timedelta(seconds=20))
    cd.trigger("queue_depth", now=now - timedelta(seconds=400))
    cd.trigger("error_rate", now=now - timedelta(seconds=10))
    return cd


@click.group()
def cooldown():
    """Manage and inspect alert cooldown windows."""


@cooldown.command("status")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]))
def show_status(fmt: str):
    """Show current cooldown status for all tracked metrics."""
    cd = _build_sample_cooldown()
    entries = cd.all_entries()

    if fmt == "json":
        click.echo(json.dumps([e.to_dict() for e in entries.values()], indent=2))
        return

    if not entries:
        click.echo("No cooldown entries recorded.")
        return

    header = f"{'METRIC':<25} {'ACTIVE':<8} {'EXPIRES AT':<25} {'DURATION (s)':<14}"
    click.echo(header)
    click.echo("-" * len(header))
    for entry in entries.values():
        active = entry.is_active()
        active_str = _colorize("yes", "red") if active else _colorize("no", "green")
        click.echo(
            f"{entry.metric_name:<25} {active_str:<8} "
            f"{entry.expires_at.strftime('%Y-%m-%d %H:%M:%S'):<25} "
            f"{entry.duration_seconds:<14}"
        )


@cooldown.command("clear")
@click.argument("metric_name")
def clear_metric(metric_name: str):
    """Clear the cooldown window for a specific metric."""
    cd = _build_sample_cooldown()
    if metric_name not in cd.all_entries():
        click.echo(f"No cooldown entry found for '{metric_name}'.", err=True)
        raise SystemExit(1)
    cd.clear(metric_name)
    click.echo(f"Cooldown cleared for '{metric_name}'.")
