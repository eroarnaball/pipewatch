"""Watchdog: detects stale metrics that haven't been updated within a TTL."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional


@dataclass
class StalenessReport:
    metric_name: str
    last_seen: datetime
    ttl_seconds: int
    checked_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def age_seconds(self) -> float:
        return (self.checked_at - self.last_seen).total_seconds()

    @property
    def is_stale(self) -> bool:
        return self.age_seconds > self.ttl_seconds

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "last_seen": self.last_seen.isoformat(),
            "ttl_seconds": self.ttl_seconds,
            "age_seconds": round(self.age_seconds, 2),
            "is_stale": self.is_stale,
        }


class MetricWatchdog:
    def __init__(self, default_ttl: int = 300):
        self.default_ttl = default_ttl
        self._last_seen: Dict[str, datetime] = {}
        self._ttls: Dict[str, int] = {}

    def register(self, metric_name: str, ttl: Optional[int] = None) -> None:
        self._ttls[metric_name] = ttl if ttl is not None else self.default_ttl

    def touch(self, metric_name: str, at: Optional[datetime] = None) -> None:
        self._last_seen[metric_name] = at or datetime.utcnow()

    def check(self, metric_name: str, now: Optional[datetime] = None) -> Optional[StalenessReport]:
        if metric_name not in self._last_seen:
            return None
        now = now or datetime.utcnow()
        ttl = self._ttls.get(metric_name, self.default_ttl)
        return StalenessReport(
            metric_name=metric_name,
            last_seen=self._last_seen[metric_name],
            ttl_seconds=ttl,
            checked_at=now,
        )

    def check_all(self, now: Optional[datetime] = None) -> List[StalenessReport]:
        now = now or datetime.utcnow()
        return [r for name in self._last_seen if (r := self.check(name, now)) is not None]

    def stale_metrics(self, now: Optional[datetime] = None) -> List[StalenessReport]:
        return [r for r in self.check_all(now) if r.is_stale]
