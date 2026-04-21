"""Runbook: attach remediation hints to metrics by status."""

from dataclasses import dataclass, field
from typing import Dict, Optional
from pipewatch.metrics import MetricStatus


@dataclass
class RunbookEntry:
    metric_name: str
    status: MetricStatus
    title: str
    steps: list

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "status": self.status.value,
            "title": self.title,
            "steps": self.steps,
        }


class RunbookRegistry:
    def __init__(self) -> None:
        self._entries: Dict[tuple, RunbookEntry] = {}

    def register(self, metric_name: str, status: MetricStatus, title: str, steps: list) -> RunbookEntry:
        key = (metric_name, status)
        entry = RunbookEntry(metric_name=metric_name, status=status, title=title, steps=steps)
        self._entries[key] = entry
        return entry

    def lookup(self, metric_name: str, status: MetricStatus) -> Optional[RunbookEntry]:
        return self._entries.get((metric_name, status))

    def all_entries(self) -> list:
        return list(self._entries.values())

    def remove(self, metric_name: str, status: MetricStatus) -> bool:
        key = (metric_name, status)
        if key in self._entries:
            del self._entries[key]
            return True
        return False
