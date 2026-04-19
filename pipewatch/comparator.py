"""Compare pipeline snapshots to detect changes between runs."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pipewatch.snapshot import MetricSnapshot, PipelineSnapshot
from pipewatch.metrics import MetricStatus


@dataclass
class MetricDiff:
    name: str
    previous_value: Optional[float]
    current_value: Optional[float]
    previous_status: Optional[MetricStatus]
    current_status: Optional[MetricStatus]

    @property
    def status_changed(self) -> bool:
        return self.previous_status != self.current_status

    @property
    def value_delta(self) -> Optional[float]:
        if self.previous_value is not None and self.current_value is not None:
            return self.current_value - self.previous_value
        return None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "previous_value": self.previous_value,
            "current_value": self.current_value,
            "previous_status": self.previous_status.value if self.previous_status else None,
            "current_status": self.current_status.value if self.current_status else None,
            "status_changed": self.status_changed,
            "value_delta": self.value_delta,
        }


@dataclass
class SnapshotComparison:
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    diffs: List[MetricDiff] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or any(d.status_changed for d in self.diffs))

    def changed_diffs(self) -> List[MetricDiff]:
        return [d for d in self.diffs if d.status_changed]

    def to_dict(self) -> dict:
        return {
            "added": self.added,
            "removed": self.removed,
            "diffs": [d.to_dict() for d in self.diffs],
            "has_changes": self.has_changes,
        }


def compare_snapshots(previous: PipelineSnapshot, current: PipelineSnapshot) -> SnapshotComparison:
    prev_map: Dict[str, MetricSnapshot] = {m.name: m for m in previous.metrics}
    curr_map: Dict[str, MetricSnapshot] = {m.name: m for m in current.metrics}

    added = [name for name in curr_map if name not in prev_map]
    removed = [name for name in prev_map if name not in curr_map]

    diffs = []
    for name in prev_map:
        if name in curr_map:
            p, c = prev_map[name], curr_map[name]
            diffs.append(MetricDiff(
                name=name,
                previous_value=p.value,
                current_value=c.value,
                previous_status=p.status,
                current_status=c.status,
            ))

    return SnapshotComparison(added=added, removed=removed, diffs=diffs)
