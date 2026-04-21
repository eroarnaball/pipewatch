"""Escalation policy: promote alerts to higher severity after repeated occurrences."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional

from pipewatch.metrics import MetricStatus


@dataclass
class EscalationPolicy:
    """Defines when a warning should be escalated to critical."""
    escalate_after: int = 3          # number of consecutive warnings before escalation
    escalate_window: int = 300       # seconds within which occurrences must happen

    def to_dict(self) -> dict:
        return {
            "escalate_after": self.escalate_after,
            "escalate_window": self.escalate_window,
        }


@dataclass
class EscalationState:
    """Tracks consecutive warning occurrences for a single metric."""
    count: int = 0
    first_seen: Optional[datetime] = None
    escalated: bool = False

    def reset(self) -> None:
        self.count = 0
        self.first_seen = None
        self.escalated = False


@dataclass
class EscalationResult:
    metric_name: str
    original_status: MetricStatus
    effective_status: MetricStatus
    escalated: bool
    consecutive_warnings: int

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "original_status": self.original_status.value,
            "effective_status": self.effective_status.value,
            "escalated": self.escalated,
            "consecutive_warnings": self.consecutive_warnings,
        }


class AlertEscalator:
    """Applies escalation policies to metric statuses."""

    def __init__(self, policy: Optional[EscalationPolicy] = None) -> None:
        self._policy = policy or EscalationPolicy()
        self._states: Dict[str, EscalationState] = {}

    def evaluate(self, metric_name: str, status: MetricStatus, now: Optional[datetime] = None) -> EscalationResult:
        now = now or datetime.utcnow()
        state = self._states.setdefault(metric_name, EscalationState())

        if status == MetricStatus.OK:
            state.reset()
            return EscalationResult(metric_name, status, status, False, 0)

        if status == MetricStatus.CRITICAL:
            state.reset()
            return EscalationResult(metric_name, status, status, False, 0)

        # status is WARNING — track it
        window = timedelta(seconds=self._policy.escalate_window)
        if state.first_seen is None or (now - state.first_seen) > window:
            state.first_seen = now
            state.count = 1
            state.escalated = False
        else:
            state.count += 1

        if state.count >= self._policy.escalate_after:
            state.escalated = True
            effective = MetricStatus.CRITICAL
        else:
            effective = MetricStatus.WARNING

        return EscalationResult(metric_name, status, effective, state.escalated, state.count)

    def reset(self, metric_name: str) -> None:
        if metric_name in self._states:
            self._states[metric_name].reset()
