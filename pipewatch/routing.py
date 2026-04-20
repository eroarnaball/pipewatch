"""Alert routing: dispatch evaluations to channels based on metric name or status."""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from pipewatch.metrics import MetricStatus
from pipewatch.thresholds import MetricEvaluation
from pipewatch.alerts import AlertChannel, AlertMessage


@dataclass
class RoutingRule:
    """A rule that maps a condition to an alert channel."""
    name: str
    channel: AlertChannel
    metric_names: Optional[List[str]] = None   # None = match all
    statuses: Optional[List[MetricStatus]] = None  # None = match all

    def matches(self, evaluation: MetricEvaluation) -> bool:
        name_ok = (
            self.metric_names is None
            or evaluation.metric.name in self.metric_names
        )
        status_ok = (
            self.statuses is None
            or evaluation.status in self.statuses
        )
        return name_ok and status_ok

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "metric_names": self.metric_names,
            "statuses": [s.value for s in self.statuses] if self.statuses else None,
        }


class AlertRouter:
    """Dispatches evaluations to matching channels based on registered rules."""

    def __init__(self) -> None:
        self._rules: List[RoutingRule] = []

    def add_rule(self, rule: RoutingRule) -> None:
        self._rules.append(rule)

    def remove_rule(self, name: str) -> bool:
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.name != name]
        return len(self._rules) < before

    def rules(self) -> List[RoutingRule]:
        return list(self._rules)

    def route(self, evaluation: MetricEvaluation) -> List[str]:
        """Send evaluation to all matching channels. Returns list of rule names fired."""
        fired: List[str] = []
        msg = AlertMessage(evaluation)
        for rule in self._rules:
            if rule.matches(evaluation):
                rule.channel.send(msg)
                fired.append(rule.name)
        return fired
