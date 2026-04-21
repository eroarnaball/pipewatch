"""Circuit breaker for alert channels — stops sending alerts when a channel fails repeatedly."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class CircuitState(str, Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocking calls after too many failures
    HALF_OPEN = "half_open"  # Testing if channel recovered


@dataclass
class CircuitBreaker:
    channel_name: str
    failure_threshold: int = 3
    recovery_timeout: int = 60  # seconds
    _failures: int = field(default=0, init=False, repr=False)
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False, repr=False)
    _opened_at: Optional[datetime] = field(default=None, init=False, repr=False)

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN and self._opened_at is not None:
            elapsed = (datetime.utcnow() - self._opened_at).total_seconds()
            if elapsed >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
        return self._state

    def is_open(self) -> bool:
        return self.state == CircuitState.OPEN

    def allow_request(self) -> bool:
        return self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)

    def record_success(self) -> None:
        self._failures = 0
        self._state = CircuitState.CLOSED
        self._opened_at = None

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self.failure_threshold:
            self._state = CircuitState.OPEN
            self._opened_at = datetime.utcnow()

    def reset(self) -> None:
        self._failures = 0
        self._state = CircuitState.CLOSED
        self._opened_at = None

    def to_dict(self) -> dict:
        return {
            "channel": self.channel_name,
            "state": self.state.value,
            "failures": self._failures,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "opened_at": self._opened_at.isoformat() if self._opened_at else None,
        }


@dataclass
class CircuitBreakerRegistry:
    failure_threshold: int = 3
    recovery_timeout: int = 60
    _breakers: dict = field(default_factory=dict, init=False, repr=False)

    def get(self, channel_name: str) -> CircuitBreaker:
        if channel_name not in self._breakers:
            self._breakers[channel_name] = CircuitBreaker(
                channel_name=channel_name,
                failure_threshold=self.failure_threshold,
                recovery_timeout=self.recovery_timeout,
            )
        return self._breakers[channel_name]

    def all_states(self) -> list:
        return [b.to_dict() for b in self._breakers.values()]
