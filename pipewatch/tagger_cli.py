"""CLI commands for metric tagging."""
import click
from pipewatch.tagger import MetricTagger


def _build_sample_tagger() -> MetricTagger:
    t = MetricTagger()
    t.tag("cpu_usage", {"env": "prod", "team": "infra"})
    t.tag("mem_usage", {"env": "prod", "team": "platform"})
    t.tag("error_rate", {"env": "staging", "team": "backend"})
    t.tag("latency_p99", {"env": "prod", "team": "backend"})
    return t


@click.group()
def tagger():
    """Metric tagging commands."""


@tagger.command("list")
@click.option("--tag-key", default=None, help="Filter by tag key.")
@click.option("--tag-value", default=None, help="Filter by tag value (requires --tag-key).")
def list_metrics(tag_key, tag_value):
    """List tagged metrics, optionally filtered."""
    t = _build_sample_tagger()
    if tag_key:
        metrics = t.filter_by_tag(tag_key, tag_value)
    else:
        metrics = t.list_metrics()
    if not metrics:
        click.echo("No metrics found.")
        return
    click.echo(f"{'METRIC':<20} {'TAGS'}")
    click.echo("-" * 50)
    for m in metrics:
        tag_str = ", ".join(f"{k}={v}" for k, v in m.tags.items())
        click.echo(f"{m.name:<20} {tag_str}")


@tagger.command("keys")
def list_keys():
    """Show all known tag keys."""
    t = _build_sample_tagger()
    keys = sorted(t.all_tags())
    if not keys:
        click.echo("No tag keys found.")
        return
    for k in keys:
        click.echo(k)
