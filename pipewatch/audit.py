"""Audit log for tracking metric evaluation events and system actions.

Provides a lightweight append-only audit trail that records who evaluated
what, when, and what the outcome was — useful for compliance and debugging.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class AuditEventType(str, Enum):
    EVALUATION = "evaluation"
    THRESHOLD_BREACH = "threshold_breach"
    ALERT_SENT = "alert_sent"
    SILENCE_APPLIED = "silence_applied"
    CONFIG_LOADED = "config_loaded"
    SUPPRESSION_APPLIED = "suppression_applied"


@dataclass
class AuditEvent:
    """A single audit log entry."""

    event_type: AuditEventType
    metric_name: str
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    actor: str = "system"
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type.value,
            "metric_name": self.metric_name,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "actor": self.actor,
            "metadata": self.metadata,
        }


class AuditLog:
    """In-memory audit log with optional size cap and filtering."""

    def __init__(self, max_entries: int = 500) -> None:
        self._entries: List[AuditEvent] = []
        self._max_entries = max_entries

    def record(
        self,
        event_type: AuditEventType,
        metric_name: str,
        message: str,
        actor: str = "system",
        metadata: Optional[dict] = None,
    ) -> AuditEvent:
        """Append a new audit event to the log."""
        event = AuditEvent(
            event_type=event_type,
            metric_name=metric_name,
            message=message,
            actor=actor,
            metadata=metadata or {},
        )
        self._entries.append(event)
        if len(self._entries) > self._max_entries:
            self._entries.pop(0)
        return event

    def all(self) -> List[AuditEvent]:
        """Return all recorded events in chronological order."""
        return list(self._entries)

    def for_metric(self, metric_name: str) -> List[AuditEvent]:
        """Return all events associated with a specific metric."""
        return [e for e in self._entries if e.metric_name == metric_name]

    def by_type(self, event_type: AuditEventType) -> List[AuditEvent]:
        """Return all events of a given type."""
        return [e for e in self._entries if e.event_type == event_type]

    def clear(self) -> None:
        """Remove all audit entries."""
        self._entries.clear()

    def to_json(self, indent: int = 2) -> str:
        """Serialize the full audit log to a JSON string."""
        return json.dumps([e.to_dict() for e in self._entries], indent=indent)

    def __len__(self) -> int:
        return len(self._entries)
