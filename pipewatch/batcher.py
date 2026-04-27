"""Alert batching: accumulate alerts over a time window before dispatching."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from pipewatch.alerts import AlertMessage


@dataclass
class BatchEntry:
    message: AlertMessage
    queued_at: datetime

    def to_dict(self) -> dict:
        return {
            "metric_name": self.message.metric_name,
            "status": self.message.status,
            "queued_at": self.queued_at.isoformat(),
        }


@dataclass
class AlertBatch:
    entries: List[BatchEntry]
    window_seconds: int
    created_at: datetime

    @property
    def size(self) -> int:
        return len(self.entries)

    def to_dict(self) -> dict:
        return {
            "size": self.size,
            "window_seconds": self.window_seconds,
            "created_at": self.created_at.isoformat(),
            "entries": [e.to_dict() for e in self.entries],
        }


class AlertBatcher:
    """Accumulates AlertMessage objects and flushes them as a batch."""

    def __init__(self, window_seconds: int = 60) -> None:
        self._window = timedelta(seconds=window_seconds)
        self._window_seconds = window_seconds
        self._queue: List[BatchEntry] = []
        self._window_start: Optional[datetime] = None

    def enqueue(self, message: AlertMessage, now: Optional[datetime] = None) -> None:
        """Add an alert to the current batch window."""
        ts = now or datetime.utcnow()
        if self._window_start is None:
            self._window_start = ts
        self._queue.append(BatchEntry(message=message, queued_at=ts))

    def is_ready(self, now: Optional[datetime] = None) -> bool:
        """Return True if the batch window has elapsed and there are queued alerts."""
        if not self._queue or self._window_start is None:
            return False
        ts = now or datetime.utcnow()
        return (ts - self._window_start) >= self._window

    def flush(self, now: Optional[datetime] = None) -> Optional[AlertBatch]:
        """Return the current batch and reset the queue, or None if empty."""
        if not self._queue:
            return None
        ts = now or datetime.utcnow()
        batch = AlertBatch(
            entries=list(self._queue),
            window_seconds=self._window_seconds,
            created_at=self._window_start or ts,
        )
        self._queue.clear()
        self._window_start = None
        return batch

    def pending_count(self) -> int:
        return len(self._queue)
