"""CLI commands for inspecting runbook entries."""

import json
import click
from pipewatch.runbook import RunbookRegistry
from pipewatch.metrics import MetricStatus


def _build_sample_registry() -> RunbookRegistry:
    reg = RunbookRegistry()
    reg.register(
        "row_count", MetricStatus.WARNING,
        "Row count below expected range",
        ["Check upstream data source", "Verify ETL schedule ran", "Alert data engineering team"],
    )
    reg.register(
        "row_count", MetricStatus.CRITICAL,
        "Row count critically low or zero",
        ["Immediately halt downstream jobs", "Page on-call engineer", "Open incident ticket"],
    )
    reg.register(
        "latency_ms", MetricStatus.WARNING,
        "Pipeline latency elevated",
        ["Check resource utilization", "Review recent deployments"],
    )
    return reg


@click.group()
def runbook():
    """Runbook: remediation hints for pipeline metrics."""


@runbook.command("list")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]))
def list_runbooks(fmt: str):
    """List all registered runbook entries."""
    reg = _build_sample_registry()
    entries = reg.all_entries()
    if not entries:
        click.echo("No runbook entries registered.")
        return
    if fmt == "json":
        click.echo(json.dumps([e.to_dict() for e in entries], indent=2))
    else:
        click.echo(f"{'METRIC':<20} {'STATUS':<12} TITLE")
        click.echo("-" * 60)
        for e in entries:
            click.echo(f"{e.metric_name:<20} {e.status.value:<12} {e.title}")


@runbook.command("lookup")
@click.argument("metric_name")
@click.argument("status")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]))
def lookup_runbook(metric_name: str, status: str, fmt: str):
    """Look up remediation steps for a metric + status."""
    try:
        s = MetricStatus(status)
    except ValueError:
        click.echo(f"Unknown status: {status}", err=True)
        raise SystemExit(1)
    reg = _build_sample_registry()
    entry = reg.lookup(metric_name, s)
    if entry is None:
        click.echo(f"No runbook entry for '{metric_name}' / '{status}'.")
        raise SystemExit(1)
    if fmt == "json":
        click.echo(json.dumps(entry.to_dict(), indent=2))
    else:
        click.echo(f"Runbook: {entry.title}")
        click.echo(f"Metric : {entry.metric_name}  Status: {entry.status.value}")
        click.echo("Steps:")
        for i, step in enumerate(entry.steps, 1):
            click.echo(f"  {i}. {step}")
