import click
from pipewatch.dependency import DependencyGraph
from pipewatch.metrics import MetricStatus


def _build_sample_graph() -> DependencyGraph:
    g = DependencyGraph()
    g.register("ingest", depends_on=[])
    g.register("transform", depends_on=["ingest"])
    g.register("load", depends_on=["transform"])
    g.register("report", depends_on=["load", "ingest"])
    return g


@click.group()
def dependency() -> None:
    """Dependency graph commands."""


@dependency.command("check")
@click.option("--critical", multiple=True, help="Metrics to mark as CRITICAL")
@click.option("--warning", multiple=True, help="Metrics to mark as WARNING")
def check_dependencies(critical: tuple, warning: tuple) -> None:
    """Check dependency violations given forced statuses."""
    graph = _build_sample_graph()
    statuses: dict = {}
    for m in critical:
        statuses[m] = MetricStatus.CRITICAL
    for m in warning:
        statuses[m] = MetricStatus.WARNING
    for name in graph.topological_order():
        if name not in statuses:
            statuses[name] = MetricStatus.OK

    violations = graph.check_violations(statuses)
    if not violations:
        click.echo("No dependency violations detected.")
        return
    for v in violations:
        click.echo(f"[VIOLATION] {v.metric} blocked by {v.blocked_by}: {v.reason}")


@dependency.command("order")
def show_order() -> None:
    """Show topological evaluation order."""
    graph = _build_sample_graph()
    order = graph.topological_order()
    click.echo("Evaluation order:")
    for i, name in enumerate(order, 1):
        click.echo(f"  {i}. {name}")
