"""Output formatters for metric evaluations."""

import json
from typing import List
from pipewatch.metrics import MetricEvaluation, MetricStatus

STATUS_COLORS = {
    MetricStatus.OK: "\033[92m",
    MetricStatus.WARNING: "\033[93m",
    MetricStatus.CRITICAL: "\033[91m",
}
RESET = "\033[0m"


def _colorize(status: MetricStatus, text: str) -> str:
    return f"{STATUS_COLORS.get(status, '')}{text}{RESET}"


def format_table(evaluations: List[MetricEvaluation], color: bool = True) -> str:
    lines = [f"{'PIPELINE':<20} {'METRIC':<20} {'VALUE':>10} {'STATUS':<10} MESSAGE"]
    lines.append("-" * 75)
    for ev in evaluations:
        status_str = ev.status.value.upper()
        if color:
            status_str = _colorize(ev.status, status_str)
        lines.append(
            f"{ev.metric.pipeline:<20} {ev.metric.name:<20} "
            f"{ev.metric.value:>10.2f} {status_str:<10} {ev.message or ''}"
        )
    return "\n".join(lines)


def format_json(evaluations: List[MetricEvaluation]) -> str:
    data = [
        {
            "pipeline": ev.metric.pipeline,
            "metric": ev.metric.name,
            "value": ev.metric.value,
            "status": ev.status.value,
            "message": ev.message,
        }
        for ev in evaluations
    ]
    return json.dumps(data, indent=2)


def format_summary(evaluations: List[MetricEvaluation]) -> str:
    counts = {s: 0 for s in MetricStatus}
    for ev in evaluations:
        counts[ev.status] += 1
    return (
        f"Total: {len(evaluations)} | "
        f"OK: {counts[MetricStatus.OK]} | "
        f"WARNING: {counts[MetricStatus.WARNING]} | "
        f"CRITICAL: {counts[MetricStatus.CRITICAL]}"
    )
