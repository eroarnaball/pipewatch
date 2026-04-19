"""Metric silencing: temporarily mute alerts for specific metrics."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional


@dataclass
class SilenceEntry:
    metric_name: str
    reason: str
    silenced_at: datetime
    expires_at: Optional[datetime] = None

    def is_active(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.utcnow()
        if self.expires_at is None:
            return True
        return now < self.expires_at

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "reason": self.reason,
            "silenced_at": self.silenced_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "active": self.is_active(),
        }


class MetricSilencer:
    def __init__(self) -> None:
        self._entries: Dict[str, SilenceEntry] = {}

    def silence(
        self,
        metric_name: str,
        reason: str,
        expires_at: Optional[datetime] = None,
        now: Optional[datetime] = None,
    ) -> SilenceEntry:
        entry = SilenceEntry(
            metric_name=metric_name,
            reason=reason,
            silenced_at=now or datetime.utcnow(),
            expires_at=expires_at,
        )
        self._entries[metric_name] = entry
        return entry

    def unsilence(self, metric_name: str) -> bool:
        if metric_name in self._entries:
            del self._entries[metric_name]
            return True
        return False

    def is_silenced(self, metric_name: str, now: Optional[datetime] = None) -> bool:
        entry = self._entries.get(metric_name)
        if entry is None:
            return False
        return entry.is_active(now)

    def active_silences(self, now: Optional[datetime] = None) -> list:
        return [e for e in self._entries.values() if e.is_active(now)]

    def purge_expired(self, now: Optional[datetime] = None) -> int:
        now = now or datetime.utcnow()
        expired = [k for k, v in self._entries.items() if not v.is_active(now)]
        for k in expired:
            del self._entries[k]
        return len(expired)
