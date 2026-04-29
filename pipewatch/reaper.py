"""Metric reaper: automatically removes metrics that have been consistently
critical or inactive beyond a configured tolerance window."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from pipewatch.metrics import MetricStatus
from pipewatch.history import MetricHistory


@dataclass
class ReaperConfig:
    critical_streak: int = 10        # consecutive critical entries to trigger reap
    inactive_seconds: float = 3600.0  # seconds with no updates before reaping

    def to_dict(self) -> dict:
        return {
            "critical_streak": self.critical_streak,
            "inactive_seconds": self.inactive_seconds,
        }


@dataclass
class ReapResult:
    metric_name: str
    reason: str
    reaped_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "reason": self.reason,
            "reaped_at": self.reaped_at.isoformat(),
        }


class MetricReaper:
    def __init__(self, config: Optional[ReaperConfig] = None) -> None:
        self._config = config or ReaperConfig()
        self._reaped: List[ReapResult] = []

    def evaluate(self, name: str, history: MetricHistory) -> Optional[ReapResult]:
        entries = history.entries
        if not entries:
            return None

        # Check inactivity
        last_ts = entries[-1].timestamp
        age = (datetime.utcnow() - last_ts).total_seconds()
        if age >= self._config.inactive_seconds:
            result = ReapResult(metric_name=name, reason="inactive")
            self._reaped.append(result)
            return result

        # Check critical streak
        streak = 0
        for entry in reversed(entries):
            if entry.evaluation.status == MetricStatus.CRITICAL:
                streak += 1
            else:
                break
        if streak >= self._config.critical_streak:
            result = ReapResult(metric_name=name, reason="critical_streak")
            self._reaped.append(result)
            return result

        return None

    def evaluate_all(self, histories: Dict[str, MetricHistory]) -> List[ReapResult]:
        results = []
        for name, history in histories.items():
            result = self.evaluate(name, history)
            if result is not None:
                results.append(result)
        return results

    @property
    def reaped(self) -> List[ReapResult]:
        return list(self._reaped)
