"""Alert inhibitor: suppress dependent alerts when a root-cause alert is already firing."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class InhibitionRule:
    """Defines a source metric that inhibits one or more target metrics."""
    source: str
    targets: List[str]
    label: str = ""

    def to_dict(self) -> dict:
        return {"source": self.source, "targets": self.targets, "label": self.label}


@dataclass
class InhibitionResult:
    metric_name: str
    inhibited: bool
    inhibited_by: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "inhibited": self.inhibited,
            "inhibited_by": self.inhibited_by,
        }


class AlertInhibitor:
    """Suppresses alerts for target metrics when their source is actively firing."""

    def __init__(self) -> None:
        self._rules: List[InhibitionRule] = []
        self._active_sources: Dict[str, datetime] = {}

    def add_rule(self, source: str, targets: List[str], label: str = "") -> InhibitionRule:
        rule = InhibitionRule(source=source, targets=list(targets), label=label)
        self._rules.append(rule)
        return rule

    def set_firing(self, metric_name: str) -> None:
        """Mark a source metric as currently firing."""
        self._active_sources[metric_name] = datetime.utcnow()

    def clear_firing(self, metric_name: str) -> None:
        """Clear the firing state for a source metric."""
        self._active_sources.pop(metric_name, None)

    def is_inhibited(self, metric_name: str) -> InhibitionResult:
        """Check whether a metric is inhibited by any active source."""
        for rule in self._rules:
            if metric_name in rule.targets and rule.source in self._active_sources:
                return InhibitionResult(
                    metric_name=metric_name,
                    inhibited=True,
                    inhibited_by=rule.source,
                )
        return InhibitionResult(metric_name=metric_name, inhibited=False)

    def active_sources(self) -> List[str]:
        return list(self._active_sources.keys())

    def rules(self) -> List[InhibitionRule]:
        return list(self._rules)
