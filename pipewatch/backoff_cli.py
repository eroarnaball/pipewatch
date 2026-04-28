"""CLI commands for inspecting alert backoff state."""
import json
import time

import click

from pipewatch.backoff import AlertBackoff


def _build_sample_backoff() -> AlertBackoff:
    backoff = AlertBackoff(base_delay=5.0, multiplier=2.0, max_delay=300.0)
    # Simulate a few check calls to build up state
    for metric in ["orders.lag", "payment.errors", "inventory.sync"]:
        backoff.check(metric)
        if metric != "inventory.sync":
            backoff.check(metric)
    return backoff


@click.group()
def backoff() -> None:
    """Manage exponential backoff state for alert retries."""


@backoff.command("status")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]))
def show_status(fmt: str) -> None:
    """Show current backoff state for all tracked metrics."""
    ab = _build_sample_backoff()
    states = ab.all_states()

    if not states:
        click.echo("No backoff state recorded.")
        return

    if fmt == "json":
        click.echo(json.dumps([s.to_dict() for s in states.values()], indent=2))
        return

    now = time.time()
    click.echo(f"{'Metric':<25} {'Attempt':>8} {'Wait (s)':>10} {'Blocked':>8}")
    click.echo("-" * 57)
    for state in states.values():
        wait = max(0.0, state.next_allowed_at - now)
        blocked = "yes" if wait > 0 else "no"
        click.echo(f"{state.metric_name:<25} {state.attempt:>8} {wait:>10.1f} {blocked:>8}")


@backoff.command("reset")
@click.argument("metric_name")
def reset_metric(metric_name: str) -> None:
    """Reset backoff state for a specific metric."""
    ab = _build_sample_backoff()
    if ab.state_for(metric_name) is None:
        click.echo(f"No backoff state found for '{metric_name}'.", err=True)
        raise SystemExit(1)
    ab.reset(metric_name)
    click.echo(f"Backoff state cleared for '{metric_name}'.")
