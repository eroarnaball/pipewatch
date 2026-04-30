"""CLI commands for the metric mapper."""
import json
import click
from pipewatch.mapper import MetricMapper


def _build_sample_mapper() -> MetricMapper:
    mapper = MetricMapper()
    mapper.register("row_count", aliases=["rows", "record_count"], description="Number of rows processed")
    mapper.register("latency_ms", aliases=["latency", "lag_ms"], description="Pipeline latency in milliseconds")
    mapper.register("error_rate", aliases=["errors", "err_pct"], description="Fraction of failed records")
    return mapper


@click.group()
def mapper():
    """Manage metric name aliases and mappings."""


@mapper.command("list")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
def list_mappings(fmt: str):
    """List all registered metric mappings."""
    m = _build_sample_mapper()
    entries = m.all_entries()
    if fmt == "json":
        click.echo(json.dumps([e.to_dict() for e in entries], indent=2))
        return
    click.echo(f"{'CANONICAL':<20} {'ALIASES':<30} DESCRIPTION")
    click.echo("-" * 70)
    for e in entries:
        aliases_str = ", ".join(e.aliases) if e.aliases else "-"
        click.echo(f"{e.canonical:<20} {aliases_str:<30} {e.description}")


@mapper.command("resolve")
@click.argument("name")
def resolve_name(name: str):
    """Resolve a metric name or alias to its canonical form."""
    m = _build_sample_mapper()
    canonical = m.resolve(name)
    if canonical is None:
        click.echo(f"No mapping found for '{name}'.", err=True)
        raise SystemExit(1)
    click.echo(f"{name} -> {canonical}")
