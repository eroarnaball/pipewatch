"""Aggregate pipeline-level status from multiple metric evaluations."""

from dataclasses import dataclass, field
from typing import List, Optional
from pipewatch.metrics import MetricEvaluation, MetricStatus


@dataclass
class PipelineStatus:
    name: str
    evaluations: List[MetricEvaluation] = field(default_factory=list)

    @property
    def overall_status(self) -> MetricStatus:
        if any(e.status == MetricStatus.CRITICAL for e in self.evaluations):
            return MetricStatus.CRITICAL
        if any(e.status == MetricStatus.WARNING for e in self.evaluations):
            return MetricStatus.WARNING
        return MetricStatus.OK

    @property
    def critical_metrics(self) -> List[MetricEvaluation]:
        return [e for e in self.evaluations if e.status == MetricStatus.CRITICAL]

    @property
    def warning_metrics(self) -> List[MetricEvaluation]:
        return [e for e in self.evaluations if e.status == MetricStatus.WARNING]

    def summary(self) -> str:
        total = len(self.evaluations)
        ok = sum(1 for e in self.evaluations if e.status == MetricStatus.OK)
        warn = len(self.warning_metrics)
        crit = len(self.critical_metrics)
        return (
            f"Pipeline '{self.name}': {total} metrics — "
            f"{ok} OK, {warn} WARNING, {crit} CRITICAL "
            f"[overall: {self.overall_status.value}]"
        )

    def to_dict(self) -> dict:
        return {
            "pipeline": self.name,
            "overall_status": self.overall_status.value,
            "total": len(self.evaluations),
            "ok": len([e for e in self.evaluations if e.status == MetricStatus.OK]),
            "warning": len(self.warning_metrics),
            "critical": len(self.critical_metrics),
            "metrics": [
                {"name": e.metric.name, "status": e.status.value, "value": e.metric.value}
                for e in self.evaluations
            ],
        }


def evaluate_pipeline(name: str, evaluations: List[MetricEvaluation]) -> PipelineStatus:
    ps = PipelineStatus(name=name, evaluations=evaluations)
    return ps
