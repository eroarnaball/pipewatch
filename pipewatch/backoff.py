"""Exponential backoff strategy for alert retries."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class BackoffState:
    metric_name: str
    attempt: int = 0
    next_allowed_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "attempt": self.attempt,
            "next_allowed_at": self.next_allowed_at,
        }


@dataclass
class BackoffResult:
    metric_name: str
    allowed: bool
    attempt: int
    wait_seconds: float

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "allowed": self.allowed,
            "attempt": self.attempt,
            "wait_seconds": round(self.wait_seconds, 3),
        }


class AlertBackoff:
    """Tracks exponential backoff state per metric alert channel."""

    def __init__(
        self,
        base_delay: float = 5.0,
        multiplier: float = 2.0,
        max_delay: float = 300.0,
    ) -> None:
        self.base_delay = base_delay
        self.multiplier = multiplier
        self.max_delay = max_delay
        self._states: Dict[str, BackoffState] = {}

    def _delay_for(self, attempt: int) -> float:
        delay = self.base_delay * (self.multiplier ** attempt)
        return min(delay, self.max_delay)

    def check(self, metric_name: str) -> BackoffResult:
        """Return whether an alert is allowed now and advance state if so."""
        now = time.time()
        state = self._states.get(metric_name)
        if state is None:
            state = BackoffState(metric_name=metric_name)
            self._states[metric_name] = state

        if now < state.next_allowed_at:
            wait = state.next_allowed_at - now
            return BackoffResult(
                metric_name=metric_name,
                allowed=False,
                attempt=state.attempt,
                wait_seconds=wait,
            )

        current_attempt = state.attempt
        delay = self._delay_for(current_attempt)
        state.attempt += 1
        state.next_allowed_at = now + delay
        return BackoffResult(
            metric_name=metric_name,
            allowed=True,
            attempt=current_attempt,
            wait_seconds=0.0,
        )

    def reset(self, metric_name: str) -> None:
        """Reset backoff state for a metric (e.g., after recovery)."""
        self._states.pop(metric_name, None)

    def state_for(self, metric_name: str) -> Optional[BackoffState]:
        return self._states.get(metric_name)

    def all_states(self) -> Dict[str, BackoffState]:
        return dict(self._states)
