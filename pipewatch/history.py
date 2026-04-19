"""Simple in-memory and file-based metric history tracking."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import List, Optional

from pipewatch.metrics import MetricEvaluation, MetricStatus


class HistoryEntry:
    def __init__(self, evaluation: MetricEvaluation, timestamp: Optional[str] = None):
        self.evaluation = evaluation
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "metric_name": self.evaluation.metric.name,
            "value": self.evaluation.metric.value,
            "status": self.evaluation.status.value,
            "message": self.evaluation.message,
        }


class MetricHistory:
    def __init__(self, max_entries: int = 100):
        self._entries: List[HistoryEntry] = []
        self.max_entries = max_entries

    def record(self, evaluation: MetricEvaluation) -> HistoryEntry:
        entry = HistoryEntry(evaluation)
        self._entries.append(entry)
        if len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries :]
        return entry

    def get_all(self) -> List[HistoryEntry]:
        return list(self._entries)

    def get_by_status(self, status: MetricStatus) -> List[HistoryEntry]:
        return [e for e in self._entries if e.evaluation.status == status]

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            json.dump([e.to_dict() for e in self._entries], f, indent=2)

    def load(self, path: str) -> None:
        if not os.path.exists(path):
            return
        with open(path) as f:
            raw = json.load(f)
        # Restore lightweight entries without full metric objects
        self._entries = [_entry_from_dict(r) for r in raw]


def _entry_from_dict(data: dict) -> HistoryEntry:
    """Reconstruct a HistoryEntry from a plain dict (no full metric object)."""
    from pipewatch.metrics import PipelineMetric, MetricEvaluation, MetricStatus

    metric = PipelineMetric(name=data["metric_name"], value=data["value"])
    status = MetricStatus(data["status"])
    evaluation = MetricEvaluation(metric=metric, status=status, message=data["message"])
    entry = HistoryEntry(evaluation, timestamp=data["timestamp"])
    return entry
