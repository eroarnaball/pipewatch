"""Integration helpers: wrap AlertChannel dispatch with circuit breaker protection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from pipewatch.alerts import AlertChannel, AlertMessage
from pipewatch.circuit_breaker import CircuitBreakerRegistry


@dataclass
class ProtectedDispatchResult:
    channel: str
    sent: bool
    blocked: bool
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "channel": self.channel,
            "sent": self.sent,
            "blocked": self.blocked,
            "error": self.error,
        }


@dataclass
class ProtectedAlertDispatcher:
    """Wraps alert channels with circuit breaker protection."""

    registry: CircuitBreakerRegistry = field(default_factory=CircuitBreakerRegistry)
    _channels: dict = field(default_factory=dict, init=False, repr=False)

    def register_channel(self, name: str, channel: AlertChannel) -> None:
        self._channels[name] = channel

    def dispatch(self, name: str, message: AlertMessage) -> ProtectedDispatchResult:
        if name not in self._channels:
            return ProtectedDispatchResult(channel=name, sent=False, blocked=False, error="unknown channel")

        cb = self.registry.get(name)

        if not cb.allow_request():
            return ProtectedDispatchResult(channel=name, sent=False, blocked=True)

        try:
            self._channels[name].send(message)
            cb.record_success()
            return ProtectedDispatchResult(channel=name, sent=True, blocked=False)
        except Exception as exc:  # noqa: BLE001
            cb.record_failure()
            return ProtectedDispatchResult(channel=name, sent=False, blocked=False, error=str(exc))

    def dispatch_all(self, message: AlertMessage) -> list:
        return [self.dispatch(name, message) for name in self._channels]
