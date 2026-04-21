"""Alert deduplication — suppress repeated alerts for the same metric/status pair."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from pipewatch.metrics import MetricStatus


@dataclass
class DeduplicationEntry:
    metric_name: str
    status: MetricStatus
    first_seen: datetime
    last_seen: datetime
    count: int = 1

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "status": self.status.value,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "count": self.count,
        }


class AlertDeduplicator:
    """Tracks recently fired alerts and suppresses duplicates within a window."""

    def __init__(self, window_seconds: int = 300) -> None:
        self.window_seconds = window_seconds
        self._entries: Dict[Tuple[str, str], DeduplicationEntry] = {}

    def _key(self, metric_name: str, status: MetricStatus) -> Tuple[str, str]:
        return (metric_name, status.value)

    def is_duplicate(self, metric_name: str, status: MetricStatus) -> bool:
        """Return True if an identical alert was already sent within the window."""
        key = self._key(metric_name, status)
        entry = self._entries.get(key)
        if entry is None:
            return False
        age = datetime.utcnow() - entry.last_seen
        return age < timedelta(seconds=self.window_seconds)

    def record(self, metric_name: str, status: MetricStatus) -> DeduplicationEntry:
        """Record that an alert was fired; update or create the entry."""
        key = self._key(metric_name, status)
        now = datetime.utcnow()
        if key in self._entries:
            entry = self._entries[key]
            entry.last_seen = now
            entry.count += 1
        else:
            entry = DeduplicationEntry(
                metric_name=metric_name,
                status=status,
                first_seen=now,
                last_seen=now,
            )
            self._entries[key] = entry
        return entry

    def clear(self, metric_name: str, status: Optional[MetricStatus] = None) -> None:
        """Remove dedup entries for a metric, optionally scoped to a status."""
        if status is not None:
            self._entries.pop(self._key(metric_name, status), None)
        else:
            for s in list(MetricStatus):
                self._entries.pop(self._key(metric_name, s), None)

    def all_entries(self) -> list:
        return [e.to_dict() for e in self._entries.values()]
