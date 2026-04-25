"""CLI commands for pipeline topology inspection."""
import json
import click
from pipewatch.topology import PipelineTopology


def _build_sample_topology() -> PipelineTopology:
    topo = PipelineTopology()
    topo.add_node("ingest", tags={"team": "data"})
    topo.add_node("transform", tags={"team": "data"})
    topo.add_node("load", tags={"team": "infra"})
    topo.add_node("report", tags={"team": "bi"})
    topo.add_edge("ingest", "transform", label="raw")
    topo.add_edge("transform", "load", label="cleaned")
    topo.add_edge("load", "report", label="aggregated")
    return topo


@click.group()
def topology():
    """Inspect pipeline metric topology."""


@topology.command("show")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]))
def show_topology(fmt: str):
    """Show all nodes and edges in the topology."""
    topo = _build_sample_topology()
    if fmt == "json":
        click.echo(json.dumps(topo.to_dict(), indent=2))
        return
    click.echo(f"{'NODE':<20} {'TAGS':<30}")
    click.echo("-" * 50)
    for node in topo.all_nodes():
        tag_str = ", ".join(f"{k}={v}" for k, v in node.tags.items())
        click.echo(f"{node.name:<20} {tag_str:<30}")
    click.echo()
    click.echo(f"{'SOURCE':<20} {'TARGET':<20} {'LABEL':<15}")
    click.echo("-" * 55)
    for edge in topo.all_edges():
        click.echo(f"{edge.source:<20} {edge.target:<20} {edge.label or '':<15}")


@topology.command("neighbors")
@click.argument("metric")
def show_neighbors(metric: str):
    """Show downstream neighbors of a metric node."""
    topo = _build_sample_topology()
    neighbors = topo.neighbors(metric)
    if not neighbors:
        click.echo(f"No downstream neighbors for '{metric}'.")
        return
    click.echo(f"Downstream of '{metric}':")
    for n in neighbors:
        click.echo(f"  -> {n}")


@topology.command("reachable")
@click.argument("metric")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]))
def show_reachable(metric: str, fmt: str):
    """Show all metrics reachable from a given node."""
    topo = _build_sample_topology()
    reachable = sorted(topo.reachable_from(metric))
    if fmt == "json":
        click.echo(json.dumps({"start": metric, "reachable": reachable}, indent=2))
        return
    if not reachable:
        click.echo(f"No nodes reachable from '{metric}'.")
        return
    click.echo(f"Reachable from '{metric}':")
    for name in reachable:
        click.echo(f"  {name}")
