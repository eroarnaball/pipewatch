"""Notification rate-limiting and deduplication for pipewatch alerts."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional

from pipewatch.metrics import MetricStatus


@dataclass
class NotificationState:
    last_sent: datetime
    last_status: MetricStatus
    count: int = 1


class NotificationThrottle:
    """Prevents duplicate/noisy alerts by rate-limiting per metric."""

    def __init__(self, cooldown_seconds: int = 300, repeat_interval_seconds: int = 3600):
        self.cooldown = timedelta(seconds=cooldown_seconds)
        self.repeat_interval = timedelta(seconds=repeat_interval_seconds)
        self._state: Dict[str, NotificationState] = {}

    def should_notify(self, metric_name: str, status: MetricStatus) -> bool:
        """Return True if a notification should be sent for this metric/status."""
        if status == MetricStatus.OK:
            if metric_name in self._state:
                del self._state[metric_name]
            return False

        now = datetime.utcnow()
        state = self._state.get(metric_name)

        if state is None:
            self._state[metric_name] = NotificationState(last_sent=now, last_status=status)
            return True

        # Status escalated — notify immediately
        if status != state.last_status:
            state.last_status = status
            state.last_sent = now
            state.count += 1
            return True

        # Within cooldown window — suppress
        if now - state.last_sent < self.cooldown:
            return False

        # Repeat notification after repeat_interval
        if now - state.last_sent >= self.repeat_interval:
            state.last_sent = now
            state.count += 1
            return True

        return False

    def reset(self, metric_name: Optional[str] = None) -> None:
        """Reset state for a specific metric or all metrics."""
        if metric_name:
            self._state.pop(metric_name, None)
        else:
            self._state.clear()

    def state_for(self, metric_name: str) -> Optional[NotificationState]:
        return self._state.get(metric_name)
