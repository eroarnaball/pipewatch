"""CLI commands for inspecting circuit breaker state."""

import json
import click
from pipewatch.circuit_breaker import CircuitBreakerRegistry


def _build_sample_registry() -> CircuitBreakerRegistry:
    registry = CircuitBreakerRegistry(failure_threshold=3, recovery_timeout=60)
    cb1 = registry.get("slack")
    cb1.record_failure()
    cb1.record_failure()

    cb2 = registry.get("pagerduty")
    cb2.record_failure()
    cb2.record_failure()
    cb2.record_failure()  # trips the breaker

    cb3 = registry.get("email")
    cb3.record_success()
    return registry


@click.group()
def circuit_breaker():
    """Inspect and manage alert channel circuit breakers."""


@circuit_breaker.command("status")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]))
def show_status(fmt: str):
    """Show current circuit breaker states."""
    registry = _build_sample_registry()
    states = registry.all_states()

    if fmt == "json":
        click.echo(json.dumps(states, indent=2))
        return

    header = f"{'CHANNEL':<20} {'STATE':<12} {'FAILURES':<10} {'THRESHOLD':<10}"
    click.echo(header)
    click.echo("-" * len(header))
    for s in states:
        click.echo(
            f"{s['channel']:<20} {s['state']:<12} {s['failures']:<10} {s['failure_threshold']:<10}"
        )


@circuit_breaker.command("reset")
@click.argument("channel")
def reset_channel(channel: str):
    """Reset circuit breaker for a channel."""
    registry = _build_sample_registry()
    cb = registry.get(channel)
    cb.reset()
    click.echo(f"Circuit breaker for '{channel}' has been reset.")


@circuit_breaker.command("detail")
@click.argument("channel")
def detail(channel: str):
    """Show detailed circuit breaker info for a channel."""
    registry = _build_sample_registry()
    cb = registry.get(channel)
    click.echo(json.dumps(cb.to_dict(), indent=2))
