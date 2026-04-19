"""Metric aggregation utilities for summarizing pipeline health over time."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pipewatch.metrics import MetricStatus, MetricEvaluation
from pipewatch.history import MetricHistory, HistoryEntry


@dataclass
class AggregatedStats:
    metric_name: str
    total: int = 0
    ok_count: int = 0
    warning_count: int = 0
    critical_count: int = 0
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    avg_value: Optional[float] = None

    def to_dict(self) -> Dict:
        return {
            "metric_name": self.metric_name,
            "total": self.total,
            "ok_count": self.ok_count,
            "warning_count": self.warning_count,
            "critical_count": self.critical_count,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "avg_value": self.avg_value,
        }


class MetricAggregator:
    def __init__(self, history: MetricHistory):
        self._history = history

    def compute(self, metric_name: str) -> AggregatedStats:
        entries: List[HistoryEntry] = [
            e for e in self._history.entries if e.metric_name == metric_name
        ]
        stats = AggregatedStats(metric_name=metric_name, total=len(entries))
        if not entries:
            return stats

        values = [e.value for e in entries if e.value is not None]
        for e in entries:
            if e.status == MetricStatus.OK:
                stats.ok_count += 1
            elif e.status == MetricStatus.WARNING:
                stats.warning_count += 1
            elif e.status == MetricStatus.CRITICAL:
                stats.critical_count += 1

        if values:
            stats.min_value = min(values)
            stats.max_value = max(values)
            stats.avg_value = sum(values) / len(values)

        return stats

    def compute_all(self) -> List[AggregatedStats]:
        names = {e.metric_name for e in self._history.entries}
        return [self.compute(name) for name in sorted(names)]
