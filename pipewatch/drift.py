"""Metric drift detection: tracks how much a metric's value has shifted over time."""

from dataclasses import dataclass, field
from typing import Optional
from pipewatch.history import MetricHistory


@dataclass
class DriftResult:
    metric_name: str
    baseline_avg: float
    recent_avg: float
    drift_absolute: float
    drift_percent: float
    is_drifting: bool

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "baseline_avg": round(self.baseline_avg, 4),
            "recent_avg": round(self.recent_avg, 4),
            "drift_absolute": round(self.drift_absolute, 4),
            "drift_percent": round(self.drift_percent, 4),
            "is_drifting": self.is_drifting,
        }


class MetricDriftDetector:
    """Detects value drift by comparing a baseline window to a recent window."""

    def __init__(self, baseline_size: int = 10, recent_size: int = 3, threshold_pct: float = 20.0):
        self.baseline_size = baseline_size
        self.recent_size = recent_size
        self.threshold_pct = threshold_pct

    def detect(self, name: str, history: MetricHistory) -> Optional[DriftResult]:
        entries = history.entries
        min_required = self.baseline_size + self.recent_size
        if len(entries) < min_required:
            return None

        values = [
            e.evaluation.metric.value
            for e in entries
            if e.evaluation.metric.value is not None
        ]
        if len(values) < min_required:
            return None

        baseline_vals = values[: self.baseline_size]
        recent_vals = values[-self.recent_size :]

        baseline_avg = sum(baseline_vals) / len(baseline_vals)
        recent_avg = sum(recent_vals) / len(recent_vals)
        drift_abs = recent_avg - baseline_avg
        drift_pct = (abs(drift_abs) / baseline_avg * 100.0) if baseline_avg != 0 else 0.0
        is_drifting = drift_pct >= self.threshold_pct

        return DriftResult(
            metric_name=name,
            baseline_avg=baseline_avg,
            recent_avg=recent_avg,
            drift_absolute=drift_abs,
            drift_percent=drift_pct,
            is_drifting=is_drifting,
        )
