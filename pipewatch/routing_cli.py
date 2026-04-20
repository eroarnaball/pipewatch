"""CLI commands for inspecting alert routing rules."""

import json
import click

from pipewatch.metrics import MetricStatus, PipelineMetric
from pipewatch.thresholds import MetricEvaluation
from pipewatch.alerts import ConsoleAlertChannel
from pipewatch.routing import AlertRouter, RoutingRule


def _build_sample_router() -> AlertRouter:
    router = AlertRouter()
    router.add_rule(RoutingRule(
        name="critical-all",
        channel=ConsoleAlertChannel(),
        statuses=[MetricStatus.CRITICAL],
    ))
    router.add_rule(RoutingRule(
        name="warning-latency",
        channel=ConsoleAlertChannel(),
        metric_names=["latency", "p99_latency"],
        statuses=[MetricStatus.WARNING],
    ))
    router.add_rule(RoutingRule(
        name="all-errors",
        channel=ConsoleAlertChannel(),
        metric_names=["error_rate"],
    ))
    return router


@click.group()
def routing():
    """Manage and inspect alert routing rules."""


@routing.command("list")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]))
def list_rules(fmt: str):
    """List all registered routing rules."""
    router = _build_sample_router()
    rules = router.rules()

    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in rules], indent=2))
        return

    click.echo(f"{'RULE':<25} {'METRICS':<30} {'STATUSES'}")
    click.echo("-" * 70)
    for rule in rules:
        metrics = ", ".join(rule.metric_names) if rule.metric_names else "*"
        statuses = ", ".join(s.value for s in rule.statuses) if rule.statuses else "*"
        click.echo(f"{rule.name:<25} {metrics:<30} {statuses}")


@routing.command("simulate")
@click.argument("metric_name")
@click.argument("status", type=click.Choice(["ok", "warning", "critical"]))
def simulate(metric_name: str, status: str):
    """Simulate routing for a given metric name and status."""
    router = _build_sample_router()
    metric = PipelineMetric(name=metric_name, value=1.0, unit="ms")
    ev = MetricEvaluation(
        metric=metric,
        status=MetricStatus(status),
        message=f"Simulated {status} for {metric_name}",
    )
    fired = router.route(ev)
    if fired:
        click.echo(f"Routed via rules: {', '.join(fired)}")
    else:
        click.echo("No matching rules — alert not dispatched.")
