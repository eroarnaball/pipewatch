"""CLI commands for inspecting escalation policy behaviour."""

import click
import json
from datetime import datetime, timedelta

from pipewatch.escalation import AlertEscalator, EscalationPolicy
from pipewatch.metrics import MetricStatus


def _build_sample_escalator() -> AlertEscalator:
    policy = EscalationPolicy(escalate_after=3, escalate_window=300)
    return AlertEscalator(policy=policy)


@click.group()
def escalation() -> None:
    """Manage and simulate alert escalation policies."""


@escalation.command("simulate")
@click.option("--metric", default="latency", show_default=True, help="Metric name to simulate.")
@click.option("--warnings", default=4, show_default=True, help="Number of consecutive WARNING events.")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]), show_default=True)
def simulate(metric: str, warnings: int, fmt: str) -> None:
    """Simulate repeated WARNING events and show escalation progression."""
    escalator = _build_sample_escalator()
    results = []
    base = datetime.utcnow()
    for i in range(warnings):
        ts = base + timedelta(seconds=i * 60)
        result = escalator.evaluate(metric, MetricStatus.WARNING, now=ts)
        results.append(result)

    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
        return

    click.echo(f"{'#':<4} {'Status':<10} {'Effective':<12} {'Escalated':<10} {'Count':<6}")
    click.echo("-" * 44)
    for i, r in enumerate(results, 1):
        esc_flag = "YES" if r.escalated else "no"
        click.echo(f"{i:<4} {r.original_status.value:<10} {r.effective_status.value:<12} {esc_flag:<10} {r.consecutive_warnings:<6}")


@escalation.command("policy")
@click.option("--after", default=3, show_default=True, help="Warnings before escalation.")
@click.option("--window", default=300, show_default=True, help="Time window in seconds.")
def show_policy(after: int, window: int) -> None:
    """Display the active escalation policy."""
    policy = EscalationPolicy(escalate_after=after, escalate_window=window)
    click.echo(json.dumps(policy.to_dict(), indent=2))
