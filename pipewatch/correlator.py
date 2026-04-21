"""Metric correlation: detect relationships between metric status changes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from pipewatch.history import MetricHistory
from pipewatch.metrics import MetricStatus


@dataclass
class CorrelationResult:
    metric_a: str
    metric_b: str
    co_occurrences: int
    total_events: int

    @property
    def score(self) -> float:
        """Correlation score in [0.0, 1.0]."""
        if self.total_events == 0:
            return 0.0
        return self.co_occurrences / self.total_events

    def to_dict(self) -> dict:
        return {
            "metric_a": self.metric_a,
            "metric_b": self.metric_b,
            "co_occurrences": self.co_occurrences,
            "total_events": self.total_events,
            "score": round(self.score, 4),
        }


class MetricCorrelator:
    """Detect which metrics tend to degrade together."""

    def __init__(self, bad_statuses: Optional[List[MetricStatus]] = None) -> None:
        self._bad = set(bad_statuses or [MetricStatus.WARNING, MetricStatus.CRITICAL])
        self._histories: Dict[str, MetricHistory] = {}

    def register(self, name: str, history: MetricHistory) -> None:
        self._histories[name] = history

    def _bad_timestamps(self, history: MetricHistory) -> List[float]:
        return [
            e.timestamp
            for e in history.entries
            if e.status in self._bad
        ]

    def correlate(
        self,
        metric_a: str,
        metric_b: str,
        window_seconds: float = 60.0,
    ) -> Optional[CorrelationResult]:
        """Return correlation between two registered metrics."""
        if metric_a not in self._histories or metric_b not in self._histories:
            return None

        ts_a = self._bad_timestamps(self._histories[metric_a])
        ts_b = self._bad_timestamps(self._histories[metric_b])

        if not ts_a and not ts_b:
            return CorrelationResult(metric_a, metric_b, 0, 0)

        co = sum(
            1 for t in ts_a if any(abs(t - s) <= window_seconds for s in ts_b)
        )
        total = max(len(ts_a), len(ts_b))
        return CorrelationResult(metric_a, metric_b, co, total)

    def top_correlations(
        self, window_seconds: float = 60.0, min_score: float = 0.5
    ) -> List[CorrelationResult]:
        """Return all metric pairs with correlation score >= min_score."""
        names = list(self._histories.keys())
        results: List[CorrelationResult] = []
        for i, a in enumerate(names):
            for b in names[i + 1 :]:
                r = self.correlate(a, b, window_seconds)
                if r and r.score >= min_score:
                    results.append(r)
        results.sort(key=lambda r: r.score, reverse=True)
        return results
