"""Group metrics by tag, label, or status for batch operations."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pipewatch.metrics import MetricStatus, MetricEvaluation


@dataclass
class MetricGroup:
    key: str
    value: str
    members: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "members": self.members,
            "count": len(self.members),
        }


class MetricGrouper:
    def __init__(self) -> None:
        self._groups: Dict[str, Dict[str, MetricGroup]] = {}

    def group_by_status(self, evaluations: List[MetricEvaluation]) -> Dict[str, MetricGroup]:
        """Group evaluations by their MetricStatus value."""
        result: Dict[str, MetricGroup] = {}
        for ev in evaluations:
            status_val = ev.status.value
            if status_val not in result:
                result[status_val] = MetricGroup(key="status", value=status_val)
            result[status_val].members.append(ev.metric.name)
        return result

    def group_by_field(self, evaluations: List[MetricEvaluation], field_name: str) -> Dict[str, MetricGroup]:
        """Group evaluations by an arbitrary attribute of the metric."""
        result: Dict[str, MetricGroup] = {}
        for ev in evaluations:
            val = str(getattr(ev.metric, field_name, "unknown"))
            if val not in result:
                result[val] = MetricGroup(key=field_name, value=val)
            result[val].members.append(ev.metric.name)
        return result

    def filter_group(self, group: MetricGroup, evaluations: List[MetricEvaluation]) -> List[MetricEvaluation]:
        """Return only evaluations whose metric name is in the given group."""
        member_set = set(group.members)
        return [ev for ev in evaluations if ev.metric.name in member_set]

    def summary(self, evaluations: List[MetricEvaluation]) -> dict:
        """Return a count breakdown by status."""
        groups = self.group_by_status(evaluations)
        return {
            status: len(g.members)
            for status, g in groups.items()
        }
