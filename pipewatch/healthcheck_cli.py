import json
import click
from pipewatch.healthcheck import HealthChecker
from pipewatch.metrics import MetricStatus


def _build_sample_checker() -> HealthChecker:
    checker = HealthChecker()

    def db_check():
        return MetricStatus.OK, "Database reachable"

    def queue_check():
        return MetricStatus.WARNING, "Queue depth above threshold"

    def cache_check():
        return MetricStatus.CRITICAL, "Cache unreachable"

    checker.register("database", db_check)
    checker.register("queue", queue_check)
    checker.register("cache", cache_check)
    return checker


@click.group()
def healthcheck():
    """Run and display pipeline health checks."""


@healthcheck.command("run")
@click.option("--format", "fmt", default="table", type=click.Choice(["table", "json"]))
def run_checks(fmt: str) -> None:
    """Run all registered health checks."""
    checker = _build_sample_checker()
    summary = checker.run_all()

    if fmt == "json":
        click.echo(json.dumps(summary.to_dict(), indent=2))
        return

    click.echo(f"Overall: {summary.overall.value.upper()}")
    click.echo(f"{'Name':<20} {'Status':<12} {'Message'}")
    click.echo("-" * 60)
    for r in summary.results:
        click.echo(f"{r.name:<20} {r.status.value:<12} {r.message}")


@healthcheck.command("detail")
@click.argument("name")
def detail(name: str) -> None:
    """Show result for a single named health check."""
    checker = _build_sample_checker()
    result = checker.run(name)
    if result is None:
        click.echo(f"No check registered for '{name}'.")
        raise SystemExit(1)
    click.echo(json.dumps(result.to_dict(), indent=2))
