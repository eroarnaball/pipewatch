from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewatch.metrics import MetricStatus
from pipewatch.history import MetricHistory, HistoryEntry


@dataclass
class HeatmapCell:
    hour: int  # 0-23
    status_counts: Dict[str, int] = field(default_factory=lambda: {"ok": 0, "warning": 0, "critical": 0})

    def dominant_status(self) -> str:
        if self.status_counts["critical"] > 0:
            return "critical"
        if self.status_counts["warning"] > 0:
            return "warning"
        return "ok"

    def to_dict(self) -> dict:
        return {
            "hour": self.hour,
            "status_counts": self.status_counts,
            "dominant_status": self.dominant_status(),
        }


@dataclass
class MetricHeatmap:
    metric_name: str
    cells: List[HeatmapCell] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "cells": [c.to_dict() for c in self.cells],
        }


class HeatmapBuilder:
    def __init__(self) -> None:
        self._histories: Dict[str, MetricHistory] = {}

    def register(self, name: str, history: MetricHistory) -> None:
        self._histories[name] = history

    def build(self, metric_name: str) -> Optional[MetricHeatmap]:
        history = self._histories.get(metric_name)
        if history is None:
            return None

        buckets: Dict[int, HeatmapCell] = {h: HeatmapCell(hour=h) for h in range(24)}

        for entry in history.entries:
            hour = entry.timestamp.hour
            status_key = entry.status.value if hasattr(entry.status, "value") else str(entry.status)
            if status_key in buckets[hour].status_counts:
                buckets[hour].status_counts[status_key] += 1

        return MetricHeatmap(
            metric_name=metric_name,
            cells=[buckets[h] for h in range(24)],
        )

    def build_all(self) -> List[MetricHeatmap]:
        return [hm for name in self._histories if (hm := self.build(name)) is not None]
