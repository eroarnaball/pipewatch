import click
import json
from datetime import datetime, timedelta
from pipewatch.audit import AuditLog, AuditEventType
from pipewatch.metrics import MetricStatus


def _build_sample_log() -> AuditLog:
    log = AuditLog(max_entries=100)
    now = datetime.utcnow()
    log.record(AuditEventType.METRIC_REGISTERED, "cpu_usage", {"source": "system"})
    log.record(AuditEventType.THRESHOLD_BREACHED, "cpu_usage", {"status": "WARNING", "value": 78.5})
    log.record(AuditEventType.ALERT_SENT, "cpu_usage", {"channel": "console"})
    log.record(AuditEventType.THRESHOLD_BREACHED, "memory", {"status": "CRITICAL", "value": 95.1})
    log.record(AuditEventType.ALERT_SUPPRESSED, "memory", {"reason": "cooldown"})
    log.record(AuditEventType.METRIC_UNREGISTERED, "disk_io", {})
    return log


@click.group()
def audit():
    """Inspect the audit log for pipeline events."""
    pass


@audit.command("list")
@click.option("--event-type", default=None, help="Filter by event type name.")
@click.option("--metric", default=None, help="Filter by metric name.")
@click.option("--limit", default=20, show_default=True, help="Max entries to show.")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]), show_default=True)
def list_events(event_type, metric, limit, fmt):
    """List audit log entries."""
    log = _build_sample_log()
    entries = log.all()

    if event_type:
        try:
            et = AuditEventType[event_type.upper()]
            entries = [e for e in entries if e.event_type == et]
        except KeyError:
            click.echo(f"Unknown event type: {event_type}", err=True)
            raise SystemExit(1)

    if metric:
        entries = [e for e in entries if e.metric_name == metric]

    entries = entries[-limit:]

    if fmt == "json":
        click.echo(json.dumps([e.to_dict() for e in entries], indent=2))
        return

    if not entries:
        click.echo("No audit entries found.")
        return

    click.echo(f"{'TIMESTAMP':<26} {'EVENT TYPE':<25} {'METRIC':<20} DETAILS")
    click.echo("-" * 90)
    for e in entries:
        ts = e.timestamp.strftime("%Y-%m-%dT%H:%M:%S")
        details = ", ".join(f"{k}={v}" for k, v in e.details.items())
        click.echo(f"{ts:<26} {e.event_type.name:<25} {e.metric_name:<20} {details}")


@audit.command("summary")
def summary():
    """Show a count of events grouped by type."""
    log = _build_sample_log()
    counts = log.counts_by_type()
    click.echo(f"{'EVENT TYPE':<30} COUNT")
    click.echo("-" * 40)
    for event_type, count in sorted(counts.items(), key=lambda x: -x[1]):
        click.echo(f"{event_type:<30} {count}")
