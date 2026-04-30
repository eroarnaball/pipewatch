"""Integration helpers: auto-tick metrics from MetricEvaluation results."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from pipewatch.metrics import MetricEvaluation
from pipewatch.ticker import MetricTicker, TickStats


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class EvaluationTickResult:
    metric_name: str
    stats: Optional[TickStats]
    interval_seconds: Optional[float]

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "interval_seconds": self.interval_seconds,
            "stats": self.stats.to_dict() if self.stats else None,
        }


class EvaluationTicker:
    """Wraps MetricTicker and auto-ticks on each evaluation processed."""

    def __init__(self, ticker: Optional[MetricTicker] = None) -> None:
        self._ticker = ticker or MetricTicker()

    def process(self, evaluation: MetricEvaluation) -> EvaluationTickResult:
        """Tick the metric referenced by the evaluation and return interval info."""
        name = evaluation.metric.name
        entry = self._ticker.tick(name, at=_now())
        stats = self._ticker.stats(name)
        return EvaluationTickResult(
            metric_name=name,
            stats=stats,
            interval_seconds=entry.interval_seconds,
        )

    def process_all(self, evaluations: List[MetricEvaluation]) -> List[EvaluationTickResult]:
        """Process a batch of evaluations, ticking each metric."""
        return [self.process(ev) for ev in evaluations]

    @property
    def ticker(self) -> MetricTicker:
        return self._ticker
