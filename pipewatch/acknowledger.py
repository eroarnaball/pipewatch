"""Alert acknowledgement tracking for pipewatch."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class AcknowledgementEntry:
    metric_name: str
    acknowledged_by: str
    reason: str
    acknowledged_at: datetime
    expires_at: Optional[datetime] = None

    def is_active(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.utcnow()
        if self.expires_at is None:
            return True
        return now < self.expires_at

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "acknowledged_by": self.acknowledged_by,
            "reason": self.reason,
            "acknowledged_at": self.acknowledged_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "active": self.is_active(),
        }


class MetricAcknowledger:
    def __init__(self) -> None:
        self._entries: Dict[str, AcknowledgementEntry] = {}

    def acknowledge(
        self,
        metric_name: str,
        acknowledged_by: str,
        reason: str,
        expires_at: Optional[datetime] = None,
    ) -> AcknowledgementEntry:
        entry = AcknowledgementEntry(
            metric_name=metric_name,
            acknowledged_by=acknowledged_by,
            reason=reason,
            acknowledged_at=datetime.utcnow(),
            expires_at=expires_at,
        )
        self._entries[metric_name] = entry
        return entry

    def unacknowledge(self, metric_name: str) -> bool:
        if metric_name in self._entries:
            del self._entries[metric_name]
            return True
        return False

    def is_acknowledged(self, metric_name: str, now: Optional[datetime] = None) -> bool:
        entry = self._entries.get(metric_name)
        if entry is None:
            return False
        if not entry.is_active(now):
            del self._entries[metric_name]
            return False
        return True

    def get(self, metric_name: str) -> Optional[AcknowledgementEntry]:
        return self._entries.get(metric_name)

    def all_active(self, now: Optional[datetime] = None) -> List[AcknowledgementEntry]:
        now = now or datetime.utcnow()
        expired = [k for k, v in self._entries.items() if not v.is_active(now)]
        for k in expired:
            del self._entries[k]
        return list(self._entries.values())
