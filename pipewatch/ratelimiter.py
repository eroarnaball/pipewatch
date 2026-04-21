from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional


@dataclass
class RateLimitEntry:
    metric_name: str
    max_alerts: int
    window_seconds: int
    timestamps: list = field(default_factory=list)

    def record(self, now: Optional[datetime] = None) -> None:
        now = now or datetime.utcnow()
        self.timestamps.append(now)
        self._prune(now)

    def _prune(self, now: datetime) -> None:
        cutoff = now - timedelta(seconds=self.window_seconds)
        self.timestamps = [t for t in self.timestamps if t > cutoff]

    def is_limited(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.utcnow()
        self._prune(now)
        return len(self.timestamps) >= self.max_alerts

    def remaining(self, now: Optional[datetime] = None) -> int:
        now = now or datetime.utcnow()
        self._prune(now)
        return max(0, self.max_alerts - len(self.timestamps))

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "max_alerts": self.max_alerts,
            "window_seconds": self.window_seconds,
            "current_count": len(self.timestamps),
            "remaining": self.remaining(),
            "is_limited": self.is_limited(),
        }


class AlertRateLimiter:
    def __init__(self, default_max: int = 5, default_window: int = 300):
        self.default_max = default_max
        self.default_window = default_window
        self._entries: Dict[str, RateLimitEntry] = {}

    def configure(self, metric_name: str, max_alerts: int, window_seconds: int) -> None:
        self._entries[metric_name] = RateLimitEntry(
            metric_name=metric_name,
            max_alerts=max_alerts,
            window_seconds=window_seconds,
        )

    def _get_or_create(self, metric_name: str) -> RateLimitEntry:
        if metric_name not in self._entries:
            self._entries[metric_name] = RateLimitEntry(
                metric_name=metric_name,
                max_alerts=self.default_max,
                window_seconds=self.default_window,
            )
        return self._entries[metric_name]

    def allow(self, metric_name: str, now: Optional[datetime] = None) -> bool:
        entry = self._get_or_create(metric_name)
        if entry.is_limited(now):
            return False
        entry.record(now)
        return True

    def status(self, metric_name: str) -> Optional[dict]:
        entry = self._entries.get(metric_name)
        return entry.to_dict() if entry else None

    def all_statuses(self) -> list:
        return [e.to_dict() for e in self._entries.values()]

    def reset(self, metric_name: str) -> bool:
        if metric_name in self._entries:
            self._entries[metric_name].timestamps.clear()
            return True
        return False
