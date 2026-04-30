"""Metric tick tracker — records evaluation timestamps and computes tick intervals."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class TickEntry:
    metric_name: str
    ticked_at: datetime
    interval_seconds: Optional[float]  # None for first tick

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "ticked_at": self.ticked_at.isoformat(),
            "interval_seconds": self.interval_seconds,
        }


@dataclass
class TickStats:
    metric_name: str
    tick_count: int
    avg_interval_seconds: Optional[float]
    min_interval_seconds: Optional[float]
    max_interval_seconds: Optional[float]
    last_ticked_at: Optional[datetime]

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "tick_count": self.tick_count,
            "avg_interval_seconds": self.avg_interval_seconds,
            "min_interval_seconds": self.min_interval_seconds,
            "max_interval_seconds": self.max_interval_seconds,
            "last_ticked_at": self.last_ticked_at.isoformat() if self.last_ticked_at else None,
        }


class MetricTicker:
    def __init__(self, max_entries: int = 200) -> None:
        self._max_entries = max_entries
        self._history: Dict[str, List[TickEntry]] = {}
        self._last_tick: Dict[str, datetime] = {}

    def tick(self, metric_name: str, at: Optional[datetime] = None) -> TickEntry:
        ts = at or _now()
        last = self._last_tick.get(metric_name)
        interval = (ts - last).total_seconds() if last else None
        entry = TickEntry(metric_name=metric_name, ticked_at=ts, interval_seconds=interval)
        bucket = self._history.setdefault(metric_name, [])
        bucket.append(entry)
        if len(bucket) > self._max_entries:
            bucket.pop(0)
        self._last_tick[metric_name] = ts
        return entry

    def stats(self, metric_name: str) -> Optional[TickStats]:
        entries = self._history.get(metric_name)
        if not entries:
            return None
        intervals = [e.interval_seconds for e in entries if e.interval_seconds is not None]
        avg = sum(intervals) / len(intervals) if intervals else None
        return TickStats(
            metric_name=metric_name,
            tick_count=len(entries),
            avg_interval_seconds=avg,
            min_interval_seconds=min(intervals) if intervals else None,
            max_interval_seconds=max(intervals) if intervals else None,
            last_ticked_at=entries[-1].ticked_at,
        )

    def all_stats(self) -> List[TickStats]:
        return [s for name in self._history if (s := self.stats(name)) is not None]

    def entries_for(self, metric_name: str) -> List[TickEntry]:
        return list(self._history.get(metric_name, []))
