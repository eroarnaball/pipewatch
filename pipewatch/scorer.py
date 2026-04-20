"""Pipeline health scoring module for pipewatch."""

from dataclasses import dataclass, field
from typing import List, Optional
from pipewatch.metrics import MetricStatus, MetricEvaluation


_STATUS_WEIGHTS = {
    MetricStatus.OK: 1.0,
    MetricStatus.WARNING: 0.5,
    MetricStatus.CRITICAL: 0.0,
}


@dataclass
class MetricScore:
    name: str
    status: MetricStatus
    weight: float
    score: float

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status.value,
            "weight": self.weight,
            "score": round(self.score, 4),
        }


@dataclass
class HealthScore:
    total_score: float
    max_score: float
    percentage: float
    grade: str
    metric_scores: List[MetricScore] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total_score": round(self.total_score, 4),
            "max_score": round(self.max_score, 4),
            "percentage": round(self.percentage, 2),
            "grade": self.grade,
            "metric_scores": [m.to_dict() for m in self.metric_scores],
        }


def _grade(percentage: float) -> str:
    if percentage >= 90:
        return "A"
    elif percentage >= 75:
        return "B"
    elif percentage >= 50:
        return "C"
    elif percentage >= 25:
        return "D"
    return "F"


class PipelineScorer:
    def __init__(self, weights: Optional[dict] = None):
        self._weights: dict = weights or {}

    def set_weight(self, metric_name: str, weight: float) -> None:
        if not (0.0 <= weight <= 10.0):
            raise ValueError(f"Weight must be between 0.0 and 10.0, got {weight}")
        self._weights[metric_name] = weight

    def score(self, evaluations: List[MetricEvaluation]) -> HealthScore:
        if not evaluations:
            return HealthScore(
                total_score=0.0,
                max_score=0.0,
                percentage=100.0,
                grade="A",
                metric_scores=[],
            )

        metric_scores = []
        total = 0.0
        max_total = 0.0

        for ev in evaluations:
            w = self._weights.get(ev.metric.name, 1.0)
            status_score = _STATUS_WEIGHTS.get(ev.status, 0.0)
            contrib = status_score * w
            total += contrib
            max_total += w
            metric_scores.append(
                MetricScore(name=ev.metric.name, status=ev.status, weight=w, score=contrib)
            )

        pct = (total / max_total * 100.0) if max_total > 0 else 100.0
        return HealthScore(
            total_score=total,
            max_score=max_total,
            percentage=pct,
            grade=_grade(pct),
            metric_scores=metric_scores,
        )
