"""CLI commands for the alert splitter."""
import json
import click
from pipewatch.splitter import AlertSplitter, SplitRule
from pipewatch.alerts import AlertMessage, ConsoleAlertChannel
from pipewatch.metrics import MetricStatus


def _build_sample_splitter() -> AlertSplitter:
    splitter = AlertSplitter()
    ch_ops = ConsoleAlertChannel()
    ch_db = ConsoleAlertChannel()
    splitter.add_rule(SplitRule(name="ops-all", channels=[ch_ops]))
    splitter.add_rule(SplitRule(name="db-critical", channels=[ch_db], metric_prefix="db.", min_severity="critical"))
    return splitter


@click.group()
def splitter():
    """Manage alert splitting rules."""


@splitter.command("list-rules")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]))
def list_rules(fmt: str) -> None:
    """List configured split rules."""
    s = _build_sample_splitter()
    rules = [r.to_dict() for r in s.rules]
    if fmt == "json":
        click.echo(json.dumps(rules, indent=2))
        return
    click.echo(f"{'RULE':<20} {'PREFIX':<15} {'MIN SEVERITY':<15} {'CHANNELS':<10}")
    click.echo("-" * 62)
    for r in rules:
        prefix = r["metric_prefix"] or "*"
        severity = r["min_severity"] or "any"
        click.echo(f"{r['name']:<20} {prefix:<15} {severity:<15} {r['channel_count']:<10}")


@splitter.command("simulate")
@click.argument("metric_name")
@click.option("--status", default="critical", type=click.Choice(["ok", "warning", "critical"]))
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]))
def simulate(metric_name: str, status: str, fmt: str) -> None:
    """Simulate dispatching an alert through the splitter."""
    s = _build_sample_splitter()
    msg = AlertMessage(metric_name=metric_name, status=status, value=1.0, message="simulated")
    result = s.dispatch(msg)
    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
        return
    click.echo(f"Metric : {metric_name}")
    click.echo(f"Status : {status}")
    click.echo(f"Dispatched to  : {', '.join(result.dispatched_to) or 'none'}")
    click.echo(f"Skipped rules  : {', '.join(result.skipped_rules) or 'none'}")
