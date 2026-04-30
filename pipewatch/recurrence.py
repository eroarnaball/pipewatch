from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from pipewatch.metrics import MetricStatus


@dataclass
class RecurrenceEntry:
    metric_name: str
    status: MetricStatus
    first_seen: datetime
    last_seen: datetime
    count: int

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "status": self.status.value,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "count": self.count,
        }


@dataclass
class RecurrenceResult:
    metric_name: str
    status: MetricStatus
    count: int
    is_recurring: bool

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "status": self.status.value,
            "count": self.count,
            "is_recurring": self.is_recurring,
        }


class RecurrenceTracker:
    """Tracks how often a metric repeatedly fires with the same non-OK status."""

    def __init__(self, threshold: int = 3) -> None:
        self.threshold = threshold
        self._entries: Dict[str, RecurrenceEntry] = {}

    def record(self, metric_name: str, status: MetricStatus) -> RecurrenceResult:
        now = datetime.utcnow()
        if status == MetricStatus.OK:
            self._entries.pop(metric_name, None)
            return RecurrenceResult(
                metric_name=metric_name,
                status=status,
                count=0,
                is_recurring=False,
            )

        existing = self._entries.get(metric_name)
        if existing and existing.status == status:
            existing.count += 1
            existing.last_seen = now
        else:
            existing = RecurrenceEntry(
                metric_name=metric_name,
                status=status,
                first_seen=now,
                last_seen=now,
                count=1,
            )
            self._entries[metric_name] = existing

        return RecurrenceResult(
            metric_name=metric_name,
            status=status,
            count=existing.count,
            is_recurring=existing.count >= self.threshold,
        )

    def get_entry(self, metric_name: str) -> Optional[RecurrenceEntry]:
        return self._entries.get(metric_name)

    def all_recurring(self) -> List[RecurrenceEntry]:
        return [
            e for e in self._entries.values() if e.count >= self.threshold
        ]

    def reset(self, metric_name: str) -> None:
        self._entries.pop(metric_name, None)
