"""Alert jitter: randomizes alert dispatch timing to avoid thundering herd."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from pipewatch.alerts import AlertMessage


@dataclass
class JitteredAlert:
    message: AlertMessage
    scheduled_at: datetime
    jitter_seconds: float

    def to_dict(self) -> dict:
        return {
            "metric": self.message.metric_name,
            "status": self.message.status,
            "scheduled_at": self.scheduled_at.isoformat(),
            "jitter_seconds": round(self.jitter_seconds, 3),
        }


@dataclass
class AlertJitter:
    max_jitter_seconds: float = 30.0
    _rng: random.Random = field(default_factory=random.Random, repr=False)

    def seed(self, value: int) -> None:
        """Seed the RNG for deterministic behaviour in tests."""
        self._rng.seed(value)

    def schedule(self, message: AlertMessage, base_time: Optional[datetime] = None) -> JitteredAlert:
        """Return a JitteredAlert with a randomized delay applied to base_time."""
        if base_time is None:
            base_time = datetime.utcnow()
        jitter = self._rng.uniform(0.0, self.max_jitter_seconds)
        scheduled_at = base_time + timedelta(seconds=jitter)
        return JitteredAlert(
            message=message,
            scheduled_at=scheduled_at,
            jitter_seconds=jitter,
        )

    def schedule_batch(self, messages: list[AlertMessage], base_time: Optional[datetime] = None) -> list[JitteredAlert]:
        """Schedule multiple alerts, each with independent jitter."""
        if base_time is None:
            base_time = datetime.utcnow()
        return [self.schedule(msg, base_time=base_time) for msg in messages]
