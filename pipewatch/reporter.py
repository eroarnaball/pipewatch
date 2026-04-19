"""Aggregate results from a single pipeline check run."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from pipewatch.metrics import MetricEvaluation, MetricStatus


@dataclass
class RunReport:
    evaluations: List[MetricEvaluation] = field(default_factory=list)

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
    def has_critical(self) -> bool:
        return self.critical_count > 0

    @property
    def has_warning(self) -> bool:
        return self.warning_count > 0

    @property
    def overall_status(self) -> MetricStatus:
        if self.has_critical:
            return MetricStatus.CRITICAL
        if self.has_warning:
            return MetricStatus.WARNING
        return MetricStatus.OK

    def summary_line(self) -> str:
        return (
            f"Run complete: {self.total} metrics | "
            f"OK={self.ok_count} WARNING={self.warning_count} "
            f"CRITICAL={self.critical_count} | "
            f"Overall: {self.overall_status.value.upper()}"
        )

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "ok_count": self.ok_count,
            "warning_count": self.warning_count,
            "critical_count": self.critical_count,
            "overall_status": self.overall_status.value,
            "evaluations": [
                {
                    "metric": e.metric.name,
                    "value": e.metric.value,
                    "unit": e.metric.unit,
                    "status": e.status.value,
                    "timestamp": str(e.metric.timestamp),
                }
                for e in self.evaluations
            ],
        }
