"""Metric ranker: ranks metrics by severity and value for prioritized alerting."""

from dataclasses import dataclass, field
from typing import List, Optional
from pipewatch.metrics import MetricStatus, MetricEvaluation


_STATUS_WEIGHT = {
    MetricStatus.CRITICAL: 2,
    MetricStatus.WARNING: 1,
    MetricStatus.OK: 0,
}


@dataclass
class RankedMetric:
    rank: int
    name: str
    status: MetricStatus
    value: float
    score: float

    def to_dict(self) -> dict:
        return {
            "rank": self.rank,
            "name": self.name,
            "status": self.status.value,
            "value": self.value,
            "score": round(self.score, 4),
        }


class MetricRanker:
    """Ranks MetricEvaluation results by a composite severity score."""

    def __init__(self, value_weight: float = 0.3, status_weight: float = 0.7):
        if not (0.0 <= value_weight <= 1.0 and 0.0 <= status_weight <= 1.0):
            raise ValueError("Weights must be between 0.0 and 1.0")
        self.value_weight = value_weight
        self.status_weight = status_weight

    def _score(self, evaluation: MetricEvaluation) -> float:
        status_score = _STATUS_WEIGHT.get(evaluation.status, 0)
        value = evaluation.metric.value if evaluation.metric.value is not None else 0.0
        return self.status_weight * status_score + self.value_weight * value

    def rank(self, evaluations: List[MetricEvaluation]) -> List[RankedMetric]:
        """Return evaluations sorted by descending severity score."""
        scored = [
            (ev, self._score(ev)) for ev in evaluations
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        result = []
        for i, (ev, score) in enumerate(scored, start=1):
            result.append(RankedMetric(
                rank=i,
                name=ev.metric.name,
                status=ev.status,
                value=ev.metric.value if ev.metric.value is not None else 0.0,
                score=score,
            ))
        return result

    def top(self, evaluations: List[MetricEvaluation], n: int = 5) -> List[RankedMetric]:
        """Return the top-n highest ranked metrics."""
        return self.rank(evaluations)[:n]
