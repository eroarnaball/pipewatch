"""Rollup: aggregate metric evaluations over time windows into summary records."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from pipewatch.metrics import MetricStatus
from pipewatch.history import MetricHistory, HistoryEntry


@dataclass
class RollupWindow:
    metric_name: str
    window_seconds: int
    start: datetime
    end: datetime
    total: int = 0
    ok_count: int = 0
    warning_count: int = 0
    critical_count: int = 0
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    avg_value: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "window_seconds": self.window_seconds,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "total": self.total,
            "ok_count": self.ok_count,
            "warning_count": self.warning_count,
            "critical_count": self.critical_count,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "avg_value": self.avg_value,
        }


class MetricRollup:
    def __init__(self, window_seconds: int = 300) -> None:
        self.window_seconds = window_seconds
        self._histories: Dict[str, MetricHistory] = {}

    def register(self, name: str, history: MetricHistory) -> None:
        self._histories[name] = history

    def compute(self, name: str, now: Optional[datetime] = None) -> Optional[RollupWindow]:
        history = self._histories.get(name)
        if history is None:
            return None

        now = now or datetime.utcnow()
        cutoff = now - timedelta(seconds=self.window_seconds)
        entries: List[HistoryEntry] = [
            e for e in history.entries if e.timestamp >= cutoff
        ]

        window = RollupWindow(
            metric_name=name,
            window_seconds=self.window_seconds,
            start=cutoff,
            end=now,
            total=len(entries),
        )

        if not entries:
            return window

        values = [e.value for e in entries if e.value is not None]
        for e in entries:
            if e.status == MetricStatus.OK:
                window.ok_count += 1
            elif e.status == MetricStatus.WARNING:
                window.warning_count += 1
            elif e.status == MetricStatus.CRITICAL:
                window.critical_count += 1

        if values:
            window.min_value = min(values)
            window.max_value = max(values)
            window.avg_value = sum(values) / len(values)

        return window

    def compute_all(self, now: Optional[datetime] = None) -> Dict[str, RollupWindow]:
        return {
            name: self.compute(name, now)
            for name in self._histories
        }
