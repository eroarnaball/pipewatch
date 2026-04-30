"""Alert splitter: fan out a single alert to multiple sub-channels based on rules."""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from pipewatch.alerts import AlertMessage, AlertChannel


@dataclass
class SplitRule:
    name: str
    channels: List[AlertChannel]
    metric_prefix: Optional[str] = None
    min_severity: Optional[str] = None  # 'warning' or 'critical'

    def matches(self, message: AlertMessage) -> bool:
        if self.metric_prefix and not message.metric_name.startswith(self.metric_prefix):
            return False
        if self.min_severity:
            order = ["ok", "warning", "critical"]
            msg_level = order.index(message.status.lower()) if message.status.lower() in order else 0
            min_level = order.index(self.min_severity.lower()) if self.min_severity.lower() in order else 0
            if msg_level < min_level:
                return False
        return True

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "metric_prefix": self.metric_prefix,
            "min_severity": self.min_severity,
            "channel_count": len(self.channels),
        }


@dataclass
class SplitResult:
    message: AlertMessage
    dispatched_to: List[str] = field(default_factory=list)
    skipped_rules: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "metric_name": self.message.metric_name,
            "status": self.message.status,
            "dispatched_to": self.dispatched_to,
            "skipped_rules": self.skipped_rules,
        }


class AlertSplitter:
    def __init__(self) -> None:
        self._rules: List[SplitRule] = []

    def add_rule(self, rule: SplitRule) -> SplitRule:
        self._rules.append(rule)
        return rule

    @property
    def rules(self) -> List[SplitRule]:
        return list(self._rules)

    def dispatch(self, message: AlertMessage) -> SplitResult:
        result = SplitResult(message=message)
        for rule in self._rules:
            if rule.matches(message):
                for channel in rule.channels:
                    channel.send(message)
                result.dispatched_to.append(rule.name)
            else:
                result.skipped_rules.append(rule.name)
        return result
