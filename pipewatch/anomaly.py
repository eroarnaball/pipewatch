"""Anomaly detection pipeline — integrates baseline tracking with metric evaluations."""

from dataclasses import dataclass
from typing import List, Optional

from pipewatch.baseline import BaselineTracker, DeviationResult
from pipewatch.history import MetricHistory
from pipewatch.metrics import MetricEvaluation


@dataclass
class AnomalyReport:
    metric_name: str
    anomalies: List[DeviationResult]

    @property
    def has_anomalies(self) -> bool:
        return any(r.is_anomaly for r in self.anomalies)

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "has_anomalies": self.has_anomalies,
            "anomaly_count": sum(1 for r in self.anomalies if r.is_anomaly),
            "results": [
                {
                    "value": r.value,
                    "is_anomaly": r.is_anomaly,
                    "z_score": r.z_score,
                }
                for r in self.anomalies
            ],
        }


class AnomalyDetector:
    def __init__(self, sensitivity: float = 2.0, min_samples: int = 5):
        self.tracker = BaselineTracker(sensitivity=sensitivity, min_samples=min_samples)

    def evaluate(self, evaluation: MetricEvaluation, history: MetricHistory) -> Optional[DeviationResult]:
        """Check a single evaluation value against history baseline."""
        if evaluation.value is None:
            return None
        return self.tracker.check_deviation(
            value=evaluation.value,
            history=history,
            metric_name=evaluation.metric.name,
        )

    def scan_history(self, history: MetricHistory, metric_name: str) -> AnomalyReport:
        """Scan all history entries for anomalies relative to the overall baseline."""
        entries = history.get_all()
        results = []
        for entry in entries:
            if entry.value is not None:
                result = self.tracker.check_deviation(entry.value, history, metric_name)
                results.append(result)
        return AnomalyReport(metric_name=metric_name, anomalies=results)
