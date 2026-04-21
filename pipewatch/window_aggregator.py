"""Sliding window aggregation for pipeline metrics over time intervals."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from pipewatch.history import HistoryEntry, MetricHistory
from pipewatch.metrics import MetricStatus


@dataclass
class WindowStats:
    metric_name: str
    window_seconds: int
    count: int
    ok_count: int
    warning_count: int
    critical_count: int
    avg_value: Optional[float]
    min_value: Optional[float]
    max_value: Optional[float]

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "window_seconds": self.window_seconds,
            "count": self.count,
            "ok_count": self.ok_count,
            "warning_count": self.warning_count,
            "critical_count": self.critical_count,
            "avg_value": self.avg_value,
            "min_value": self.min_value,
            "max_value": self.max_value,
        }


class WindowAggregator:
    def __init__(self, window_seconds: int = 300):
        self._window_seconds = window_seconds

    def compute(self, metric_name: str, history: MetricHistory) -> Optional[WindowStats]:
        entries = history.entries_for(metric_name)
        if not entries:
            return None

        cutoff = datetime.utcnow() - timedelta(seconds=self._window_seconds)
        window_entries: List[HistoryEntry] = [
            e for e in entries if e.timestamp >= cutoff
        ]

        if not window_entries:
            return WindowStats(
                metric_name=metric_name,
                window_seconds=self._window_seconds,
                count=0,
                ok_count=0,
                warning_count=0,
                critical_count=0,
                avg_value=None,
                min_value=None,
                max_value=None,
            )

        ok = sum(1 for e in window_entries if e.status == MetricStatus.OK)
        warning = sum(1 for e in window_entries if e.status == MetricStatus.WARNING)
        critical = sum(1 for e in window_entries if e.status == MetricStatus.CRITICAL)

        values = [e.value for e in window_entries if e.value is not None]
        avg_value = sum(values) / len(values) if values else None
        min_value = min(values) if values else None
        max_value = max(values) if values else None

        return WindowStats(
            metric_name=metric_name,
            window_seconds=self._window_seconds,
            count=len(window_entries),
            ok_count=ok,
            warning_count=warning,
            critical_count=critical,
            avg_value=avg_value,
            min_value=min_value,
            max_value=max_value,
        )
