"""Metric profiling: tracks runtime execution duration for pipeline checks."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ProfileEntry:
    metric_name: str
    duration_ms: float
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "duration_ms": round(self.duration_ms, 3),
            "timestamp": self.timestamp,
        }


@dataclass
class ProfileSummary:
    metric_name: str
    count: int
    min_ms: float
    max_ms: float
    avg_ms: float

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "count": self.count,
            "min_ms": round(self.min_ms, 3),
            "max_ms": round(self.max_ms, 3),
            "avg_ms": round(self.avg_ms, 3),
        }


class MetricProfiler:
    def __init__(self, max_entries: int = 200) -> None:
        self._max_entries = max_entries
        self._entries: List[ProfileEntry] = []

    def record(self, metric_name: str, duration_ms: float) -> ProfileEntry:
        entry = ProfileEntry(metric_name=metric_name, duration_ms=duration_ms)
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries.pop(0)
        return entry

    def entries_for(self, metric_name: str) -> List[ProfileEntry]:
        return [e for e in self._entries if e.metric_name == metric_name]

    def summarize(self, metric_name: str) -> Optional[ProfileSummary]:
        entries = self.entries_for(metric_name)
        if not entries:
            return None
        durations = [e.duration_ms for e in entries]
        return ProfileSummary(
            metric_name=metric_name,
            count=len(durations),
            min_ms=min(durations),
            max_ms=max(durations),
            avg_ms=sum(durations) / len(durations),
        )

    def all_summaries(self) -> List[ProfileSummary]:
        names: Dict[str, bool] = {}
        for e in self._entries:
            names[e.metric_name] = True
        return [s for name in names if (s := self.summarize(name)) is not None]

    def clear(self, metric_name: Optional[str] = None) -> None:
        if metric_name is None:
            self._entries.clear()
        else:
            self._entries = [e for e in self._entries if e.metric_name != metric_name]
