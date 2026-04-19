"""Aggregate pipeline run reporting using history and formatters."""

from __future__ import annotations

from typing import List

from pipewatch.history import MetricHistory
from pipewatch.metrics import MetricEvaluation, MetricStatus


class RunReport:
    """Summary report for a single pipeline check run."""

    def __init__(self, evaluations: List[MetricEvaluation]):
        self.evaluations = evaluations

    @property
    def total(self) -> int:
        return len(self.evaluations)

    @property
    def ok_count(self) -> int:
        return sum(1 for e in self.evaluations if e.status == MetricStatus.OK)

    @property
    def warning_count(self) -> int:
        return sum(1 for e in self.evaluations if e.status == MetricStatus.WARNING)

    @property
    def critical_count(self) -> int:
        return sum(1 for e in self.evaluations if e.status == MetricStatus.CRITICAL)

    @property
    def overall_status(self) -> MetricStatus:
        if self.critical_count > 0:
            return MetricStatus.CRITICAL
        if self.warning_count > 0:
            return MetricStatus.WARNING
        return MetricStatus.OK

    def summary_line(self) -> str:
        status = self.overall_status.value.upper()
        return (
            f"[{status}] {self.total} metrics checked — "
            f"{self.ok_count} ok, {self.warning_count} warning, {self.critical_count} critical"
        )


class Reporter:
    """Records evaluations to history and produces run reports."""

    def __init__(self, history: MetricHistory):
        self.history = history

    def record_run(self, evaluations: List[MetricEvaluation]) -> RunReport:
        for ev in evaluations:
            self.history.record(ev)
        return RunReport(evaluations)

    def recent_critical_count(self, last_n: int = 10) -> int:
        entries = self.history.get_all()[-last_n:]
        return sum(1 for e in entries if e.evaluation.status == MetricStatus.CRITICAL)
