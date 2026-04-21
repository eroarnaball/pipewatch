"""CLI commands for pipeline digest summaries."""

import json
import click
from datetime import datetime
from pipewatch.digest import DigestBuilder
from pipewatch.score_history import ScoreEntry
from pipewatch.metrics import MetricStatus


def _build_sample_entries() -> list:
    now = datetime.utcnow()
    return [
        ScoreEntry(metric_name="ingest.lag", score=0.2, status=MetricStatus.CRITICAL, timestamp=now),
        ScoreEntry(metric_name="transform.rate", score=0.75, status=MetricStatus.WARNING, timestamp=now),
        ScoreEntry(metric_name="output.rows", score=1.0, status=MetricStatus.OK, timestamp=now),
        ScoreEntry(metric_name="db.latency", score=1.0, status=MetricStatus.OK, timestamp=now),
        ScoreEntry(metric_name="queue.depth", score=0.4, status=MetricStatus.WARNING, timestamp=now),
    ]


@click.group()
def digest():
    """Pipeline health digest summaries."""


@digest.command("show")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]), show_default=True)
@click.option("--max-issues", default=5, show_default=True, help="Max top issues to display.")
def show_digest(fmt: str, max_issues: int):
    """Show a digest summary of current pipeline health."""
    entries = _build_sample_entries()
    builder = DigestBuilder(max_issues=max_issues)
    digest_entry = builder.build(entries)

    if digest_entry is None:
        click.echo("No data available for digest.")
        return

    if fmt == "json":
        click.echo(json.dumps(digest_entry.to_dict(), indent=2))
    else:
        click.echo(f"Digest Summary — {digest_entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        click.echo(f"  OK:       {digest_entry.ok_count}")
        click.echo(f"  Warning:  {digest_entry.warning_count}")
        click.echo(f"  Critical: {digest_entry.critical_count}")
        click.echo(f"  Avg Score: {digest_entry.avg_score:.3f}")
        if digest_entry.top_issues:
            click.echo("  Top Issues:")
            for issue in digest_entry.top_issues:
                click.echo(f"    - {issue}")
        else:
            click.echo("  Top Issues: none")
