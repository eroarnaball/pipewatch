"""Score history tracking: record and query health score over time."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class ScoreEntry:
    """A single recorded health score at a point in time."""
    timestamp: datetime
    score: float  # 0.0 - 100.0
    grade: str
    ok_count: int
    warning_count: int
    critical_count: int

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "score": round(self.score, 2),
            "grade": self.grade,
            "ok_count": self.ok_count,
            "warning_count": self.warning_count,
            "critical_count": self.critical_count,
        }


class ScoreHistory:
    """Maintains a rolling history of health scores."""

    def __init__(self, max_entries: int = 100) -> None:
        self.max_entries = max_entries
        self._entries: List[ScoreEntry] = []

    def record(self, entry: ScoreEntry) -> None:
        self._entries.append(entry)
        if len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries:]

    @property
    def entries(self) -> List[ScoreEntry]:
        return list(self._entries)

    def latest(self) -> Optional[ScoreEntry]:
        return self._entries[-1] if self._entries else None

    def average_score(self) -> float:
        if not self._entries:
            return 0.0
        return sum(e.score for e in self._entries) / len(self._entries)

    def lowest_score(self) -> Optional[ScoreEntry]:
        if not self._entries:
            return None
        return min(self._entries, key=lambda e: e.score)

    def highest_score(self) -> Optional[ScoreEntry]:
        if not self._entries:
            return None
        return max(self._entries, key=lambda e: e.score)

    def since(self, cutoff: datetime) -> List[ScoreEntry]:
        return [e for e in self._entries if e.timestamp >= cutoff]

    def to_dict(self) -> dict:
        return {
            "max_entries": self.max_entries,
            "count": len(self._entries),
            "average_score": round(self.average_score(), 2),
            "entries": [e.to_dict() for e in self._entries],
        }
