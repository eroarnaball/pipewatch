"""Suppression rules for silencing alerts during maintenance windows or known issues."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class SuppressionRule:
    metric_name: str
    reason: str
    start: datetime
    end: Optional[datetime] = None  # None means indefinite

    def is_active(self, at: Optional[datetime] = None) -> bool:
        now = at or datetime.utcnow()
        if now < self.start:
            return False
        if self.end is not None and now > self.end:
            return False
        return True

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "reason": self.reason,
            "start": self.start.isoformat(),
            "end": self.end.isoformat() if self.end else None,
            "active": self.is_active(),
        }


class AlertSuppressor:
    def __init__(self) -> None:
        self._rules: list[SuppressionRule] = []

    def add_rule(self, rule: SuppressionRule) -> None:
        self._rules.append(rule)

    def remove_rules_for(self, metric_name: str) -> int:
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.metric_name != metric_name]
        return before - len(self._rules)

    def is_suppressed(self, metric_name: str, at: Optional[datetime] = None) -> bool:
        return any(
            r.metric_name == metric_name and r.is_active(at)
            for r in self._rules
        )

    def active_rules(self, at: Optional[datetime] = None) -> list[SuppressionRule]:
        return [r for r in self._rules if r.is_active(at)]

    def all_rules(self) -> list[SuppressionRule]:
        return list(self._rules)
