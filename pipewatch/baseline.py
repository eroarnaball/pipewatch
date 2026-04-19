"""Baseline tracking for pipeline metrics — detects deviations from historical norms."""

from dataclasses import dataclass, field
from typing import Optional
from statistics import mean, stdev

from pipewatch.history import MetricHistory


@dataclass
class BaselineStats:
    metric_name: str
    sample_count: int
    mean: float
    stddev: float
    lower_bound: float
    upper_bound: float

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "sample_count": self.sample_count,
            "mean": round(self.mean, 4),
            "stddev": round(self.stddev, 4),
            "lower_bound": round(self.lower_bound, 4),
            "upper_bound": round(self.upper_bound, 4),
        }


@dataclass
class DeviationResult:
    metric_name: str
    value: float
    is_anomaly: bool
    z_score: Optional[float]
    baseline: Optional[BaselineStats]


class BaselineTracker:
    def __init__(self, sensitivity: float = 2.0, min_samples: int = 5):
        self.sensitivity = sensitivity
        self.min_samples = min_samples

    def compute_baseline(self, history: MetricHistory, metric_name: str) -> Optional[BaselineStats]:
        entries = history.get_all()
        values = [e.value for e in entries if e.value is not None]
        if len(values) < self.min_samples:
            return None
        m = mean(values)
        s = stdev(values) if len(values) > 1 else 0.0
        return BaselineStats(
            metric_name=metric_name,
            sample_count=len(values),
            mean=m,
            stddev=s,
            lower_bound=m - self.sensitivity * s,
            upper_bound=m + self.sensitivity * s,
        )

    def check_deviation(self, value: float, history: MetricHistory, metric_name: str) -> DeviationResult:
        baseline = self.compute_baseline(history, metric_name)
        if baseline is None:
            return DeviationResult(metric_name=metric_name, value=value, is_anomaly=False, z_score=None, baseline=None)
        z = (value - baseline.mean) / baseline.stddev if baseline.stddev > 0 else 0.0
        is_anomaly = abs(z) > self.sensitivity
        return DeviationResult(metric_name=metric_name, value=value, is_anomaly=is_anomaly, z_score=round(z, 4), baseline=baseline)
