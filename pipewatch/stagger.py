"""Staggered alert dispatcher — spreads alerts over time to avoid notification storms."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.metrics import MetricStatus
from pipewatch.alerts import AlertMessage


@dataclass
class StaggeredAlert:
    message: AlertMessage
    scheduled_at: float  # epoch seconds
    sent: bool = False

    def to_dict(self) -> dict:
        return {
            "metric": self.message.metric_name,
            "status": self.message.status.value,
            "scheduled_at": self.scheduled_at,
            "sent": self.sent,
        }


class AlertStagger:
    """Queues alerts and releases them at a configurable interval (seconds)."""

    def __init__(self, interval_seconds: float = 5.0) -> None:
        self.interval_seconds = interval_seconds
        self._queue: List[StaggeredAlert] = []
        self._last_sent_at: Optional[float] = None

    def enqueue(self, message: AlertMessage) -> StaggeredAlert:
        """Add an alert to the stagger queue."""
        now = time.time()
        if not self._queue:
            scheduled = now
        else:
            last = max(a.scheduled_at for a in self._queue)
            scheduled = max(now, last + self.interval_seconds)
        entry = StaggeredAlert(message=message, scheduled_at=scheduled)
        self._queue.append(entry)
        return entry

    def due(self, now: Optional[float] = None) -> List[StaggeredAlert]:
        """Return alerts that are due to be sent."""
        ts = now if now is not None else time.time()
        return [a for a in self._queue if not a.sent and a.scheduled_at <= ts]

    def mark_sent(self, alert: StaggeredAlert) -> None:
        alert.sent = True
        self._last_sent_at = alert.scheduled_at

    def flush(self, now: Optional[float] = None) -> List[StaggeredAlert]:
        """Mark all due alerts as sent and return them."""
        ready = self.due(now=now)
        for a in ready:
            self.mark_sent(a)
        return ready

    def pending(self) -> List[StaggeredAlert]:
        return [a for a in self._queue if not a.sent]

    def queue_size(self) -> int:
        return len(self.pending())

    def cancel(self, metric_name: str) -> int:
        """Remove all unsent alerts for a given metric from the queue.

        Useful when a metric recovers before its queued alerts are dispatched,
        allowing stale notifications to be discarded.

        Returns the number of alerts removed.
        """
        before = len(self._queue)
        self._queue = [
            a for a in self._queue
            if a.sent or a.message.metric_name != metric_name
        ]
        return before - len(self._queue)
