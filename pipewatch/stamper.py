"""Metric stamper: attaches versioned timestamps to evaluations for lineage tracking."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewatch.metrics import MetricEvaluation


@dataclass
class StampedEvaluation:
    evaluation: MetricEvaluation
    stamped_at: float
    stamp_id: str
    sequence: int

    def to_dict(self) -> dict:
        return {
            "metric_name": self.evaluation.metric.name,
            "status": self.evaluation.status.value,
            "value": self.evaluation.metric.value,
            "stamped_at": self.stamped_at,
            "stamp_id": self.stamp_id,
            "sequence": self.sequence,
        }


class MetricStamper:
    """Attaches a monotonically increasing sequence number and unique stamp ID
    to each evaluation for audit and lineage purposes."""

    def __init__(self) -> None:
        self._counters: Dict[str, int] = {}
        self._history: Dict[str, List[StampedEvaluation]] = {}

    def stamp(self, evaluation: MetricEvaluation) -> StampedEvaluation:
        name = evaluation.metric.name
        seq = self._counters.get(name, 0) + 1
        self._counters[name] = seq
        now = time.time()
        raw = f"{name}:{evaluation.status.value}:{now}:{seq}"
        stamp_id = hashlib.sha1(raw.encode()).hexdigest()[:12]
        stamped = StampedEvaluation(
            evaluation=evaluation,
            stamped_at=now,
            stamp_id=stamp_id,
            sequence=seq,
        )
        self._history.setdefault(name, []).append(stamped)
        return stamped

    def history_for(self, name: str) -> List[StampedEvaluation]:
        return list(self._history.get(name, []))

    def latest(self, name: str) -> Optional[StampedEvaluation]:
        entries = self._history.get(name, [])
        return entries[-1] if entries else None

    def all_names(self) -> List[str]:
        return list(self._counters.keys())
