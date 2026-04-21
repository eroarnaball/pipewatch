"""Flap detection: identifies metrics that oscillate rapidly between statuses."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from pipewatch.metrics import MetricStatus


@dataclass
class FlapEvent:
    metric_name: str
    from_status: MetricStatus
    to_status: MetricStatus
    timestamp: datetime

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "from_status": self.from_status.value,
            "to_status": self.to_status.value,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class FlapResult:
    metric_name: str
    is_flapping: bool
    transition_count: int
    flap_rate: float  # transitions per entry in window
    events: List[FlapEvent] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "is_flapping": self.is_flapping,
            "transition_count": self.transition_count,
            "flap_rate": round(self.flap_rate, 4),
            "events": [e.to_dict() for e in self.events],
        }


class FlapDetector:
    """Detects flapping metrics by counting status transitions within a window."""

    def __init__(self, window: int = 10, threshold: float = 0.4):
        """
        Args:
            window: number of recent history entries to examine.
            threshold: fraction of transitions vs entries that triggers flap detection.
        """
        self.window = window
        self.threshold = threshold

    def detect(self, metric_name: str, history: "MetricHistory") -> Optional[FlapResult]:  # noqa: F821
        entries = history.get_recent(self.window)
        if len(entries) < 2:
            return None

        events: List[FlapEvent] = []
        for i in range(1, len(entries)):
            prev = entries[i - 1]
            curr = entries[i]
            if curr.status != prev.status:
                events.append(
                    FlapEvent(
                        metric_name=metric_name,
                        from_status=prev.status,
                        to_status=curr.status,
                        timestamp=curr.timestamp,
                    )
                )

        transition_count = len(events)
        flap_rate = transition_count / len(entries)
        is_flapping = flap_rate >= self.threshold

        return FlapResult(
            metric_name=metric_name,
            is_flapping=is_flapping,
            transition_count=transition_count,
            flap_rate=flap_rate,
            events=events,
        )
