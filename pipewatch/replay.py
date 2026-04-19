"""Replay historical metric evaluations for debugging and analysis."""

from dataclasses import dataclass, field
from typing import List, Optional
from pipewatch.history import MetricHistory, HistoryEntry
from pipewatch.metrics import MetricStatus


@dataclass
class ReplayFrame:
    index: int
    entry: HistoryEntry

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "entry": self.entry.to_dict(),
        }


class MetricReplayer:
    def __init__(self, history: MetricHistory):
        self._history = history
        self._frames: List[ReplayFrame] = [
            ReplayFrame(index=i, entry=e)
            for i, e in enumerate(history.entries)
        ]

    def frames(self) -> List[ReplayFrame]:
        return list(self._frames)

    def slice(self, start: int, end: int) -> List[ReplayFrame]:
        return [f for f in self._frames if start <= f.index < end]

    def filter_by_status(self, status: MetricStatus) -> List[ReplayFrame]:
        return [f for f in self._frames if f.entry.status == status]

    def first_occurrence(self, status: MetricStatus) -> Optional[ReplayFrame]:
        for frame in self._frames:
            if frame.entry.status == status:
                return frame
        return None

    def summary(self) -> dict:
        counts = {s: 0 for s in MetricStatus}
        for f in self._frames:
            counts[f.entry.status] += 1
        return {
            "total": len(self._frames),
            "ok": counts[MetricStatus.OK],
            "warning": counts[MetricStatus.WARNING],
            "critical": counts[MetricStatus.CRITICAL],
        }
