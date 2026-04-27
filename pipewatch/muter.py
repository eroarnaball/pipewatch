"""Alert muter: temporarily mute alerts for specific metrics by pattern or name."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class MuteEntry:
    metric_pattern: str
    reason: str
    muted_at: datetime
    expires_at: Optional[datetime]

    def is_active(self, at: Optional[datetime] = None) -> bool:
        t = at or _now()
        if self.expires_at is None:
            return True
        return t < self.expires_at

    def matches(self, metric_name: str) -> bool:
        return fnmatch.fnmatch(metric_name, self.metric_pattern)

    def to_dict(self) -> dict:
        return {
            "metric_pattern": self.metric_pattern,
            "reason": self.reason,
            "muted_at": self.muted_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "active": self.is_active(),
        }


class AlertMuter:
    def __init__(self) -> None:
        self._entries: list[MuteEntry] = []

    def mute(
        self,
        metric_pattern: str,
        reason: str,
        duration_seconds: Optional[float] = None,
        at: Optional[datetime] = None,
    ) -> MuteEntry:
        now = at or _now()
        expires_at = None
        if duration_seconds is not None:
            from datetime import timedelta
            expires_at = now + timedelta(seconds=duration_seconds)
        entry = MuteEntry(
            metric_pattern=metric_pattern,
            reason=reason,
            muted_at=now,
            expires_at=expires_at,
        )
        self._entries.append(entry)
        return entry

    def unmute(self, metric_pattern: str) -> bool:
        before = len(self._entries)
        self._entries = [
            e for e in self._entries if e.metric_pattern != metric_pattern
        ]
        return len(self._entries) < before

    def is_muted(self, metric_name: str, at: Optional[datetime] = None) -> bool:
        t = at or _now()
        return any(
            e.is_active(t) and e.matches(metric_name) for e in self._entries
        )

    def active_entries(self, at: Optional[datetime] = None) -> list[MuteEntry]:
        t = at or _now()
        return [e for e in self._entries if e.is_active(t)]

    def purge_expired(self, at: Optional[datetime] = None) -> int:
        t = at or _now()
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.is_active(t)]
        return before - len(self._entries)
