"""Cooldown tracker: prevents repeated alerts during a recovery window."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional

from pipewatch.metrics import MetricStatus


@dataclass
class CooldownEntry:
    metric_name: str
    triggered_at: datetime
    duration_seconds: float

    @property
    def expires_at(self) -> datetime:
        return self.triggered_at + timedelta(seconds=self.duration_seconds)

    def is_active(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.utcnow()
        return now < self.expires_at

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "triggered_at": self.triggered_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "duration_seconds": self.duration_seconds,
            "active": self.is_active(),
        }


class AlertCooldown:
    """Tracks per-metric cooldown windows after an alert fires."""

    def __init__(self, default_seconds: float = 300.0):
        self.default_seconds = default_seconds
        self._entries: Dict[str, CooldownEntry] = {}
        self._overrides: Dict[str, float] = {}

    def set_override(self, metric_name: str, seconds: float) -> None:
        """Set a custom cooldown duration for a specific metric."""
        self._overrides[metric_name] = seconds

    def trigger(self, metric_name: str, now: Optional[datetime] = None) -> CooldownEntry:
        """Start a cooldown window for the given metric."""
        now = now or datetime.utcnow()
        duration = self._overrides.get(metric_name, self.default_seconds)
        entry = CooldownEntry(
            metric_name=metric_name,
            triggered_at=now,
            duration_seconds=duration,
        )
        self._entries[metric_name] = entry
        return entry

    def is_cooling(self, metric_name: str, now: Optional[datetime] = None) -> bool:
        """Return True if the metric is currently in a cooldown window."""
        entry = self._entries.get(metric_name)
        if entry is None:
            return False
        return entry.is_active(now)

    def clear(self, metric_name: str) -> None:
        """Manually clear a cooldown for a metric (e.g. on recovery)."""
        self._entries.pop(metric_name, None)

    def all_entries(self) -> Dict[str, CooldownEntry]:
        return dict(self._entries)
