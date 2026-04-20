"""Tracks historical health scores over time for pipewatch."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from pipewatch.scorer import HealthScore


@dataclass
class ScoreEntry:
    timestamp: datetime
    percentage: float
    grade: str

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "percentage": round(self.percentage, 2),
            "grade": self.grade,
        }


class ScoreHistory:
    def __init__(self, max_entries: int = 100):
        if max_entries < 1:
            raise ValueError("max_entries must be at least 1")
        self._max_entries = max_entries
        self._entries: List[ScoreEntry] = []

    def record(self, score: HealthScore, timestamp: Optional[datetime] = None) -> ScoreEntry:
        ts = timestamp or datetime.utcnow()
        entry = ScoreEntry(timestamp=ts, percentage=score.percentage, grade=score.grade)
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries.pop(0)
        return entry

    def latest(self) -> Optional[ScoreEntry]:
        return self._entries[-1] if self._entries else None

    def all_entries(self) -> List[ScoreEntry]:
        return list(self._entries)

    def average_percentage(self) -> Optional[float]:
        if not self._entries:
            return None
        return sum(e.percentage for e in self._entries) / len(self._entries)

    def trend(self) -> str:
        """Return 'improving', 'degrading', or 'stable' based on last vs first entry."""
        if len(self._entries) < 2:
            return "stable"
        delta = self._entries[-1].percentage - self._entries[0].percentage
        if delta > 5.0:
            return "improving"
        elif delta < -5.0:
            return "degrading"
        return "stable"

    def to_dict(self) -> dict:
        avg = self.average_percentage()
        return {
            "entries": [e.to_dict() for e in self._entries],
            "average_percentage": round(avg, 2) if avg is not None else None,
            "trend": self.trend(),
            "count": len(self._entries),
        }
