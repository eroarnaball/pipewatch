"""Persistent log of dispatched alert messages with query support."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from pipewatch.metrics import MetricStatus


@dataclass
class DispatchRecord:
    metric_name: str
    status: MetricStatus
    channel: str
    message: str
    dispatched_at: datetime = field(default_factory=datetime.utcnow)
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "status": self.status.value,
            "channel": self.channel,
            "message": self.message,
            "dispatched_at": self.dispatched_at.isoformat(),
            "success": self.success,
            "error": self.error,
        }


class DispatcherLog:
    def __init__(self, max_entries: int = 500) -> None:
        self._records: List[DispatchRecord] = []
        self._max_entries = max_entries

    def record(self, record: DispatchRecord) -> DispatchRecord:
        self._records.append(record)
        if len(self._records) > self._max_entries:
            self._records = self._records[-self._max_entries :]
        return record

    def all(self) -> List[DispatchRecord]:
        return list(self._records)

    def for_metric(self, metric_name: str) -> List[DispatchRecord]:
        return [r for r in self._records if r.metric_name == metric_name]

    def for_channel(self, channel: str) -> List[DispatchRecord]:
        return [r for r in self._records if r.channel == channel]

    def failures(self) -> List[DispatchRecord]:
        return [r for r in self._records if not r.success]

    def by_status(self, status: MetricStatus) -> List[DispatchRecord]:
        return [r for r in self._records if r.status == status]

    def clear(self) -> None:
        self._records.clear()

    def total(self) -> int:
        return len(self._records)
