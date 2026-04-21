"""Periodic digest summaries for pipeline health reports."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from pipewatch.metrics import MetricStatus
from pipewatch.score_history import ScoreEntry


@dataclass
class DigestEntry:
    timestamp: datetime
    ok_count: int
    warning_count: int
    critical_count: int
    avg_score: float
    top_issues: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "ok_count": self.ok_count,
            "warning_count": self.warning_count,
            "critical_count": self.critical_count,
            "avg_score": round(self.avg_score, 3),
            "top_issues": self.top_issues,
        }


class DigestBuilder:
    """Builds a DigestEntry from a list of ScoreEntries."""

    def __init__(self, max_issues: int = 5):
        self.max_issues = max_issues

    def build(self, entries: List[ScoreEntry], timestamp: Optional[datetime] = None) -> Optional[DigestEntry]:
        if not entries:
            return None

        ts = timestamp or datetime.utcnow()
        ok = sum(1 for e in entries if e.status == MetricStatus.OK)
        warning = sum(1 for e in entries if e.status == MetricStatus.WARNING)
        critical = sum(1 for e in entries if e.status == MetricStatus.CRITICAL)
        avg_score = sum(e.score for e in entries) / len(entries)

        issues = [
            e.metric_name
            for e in sorted(entries, key=lambda x: x.score)
            if e.status != MetricStatus.OK
        ][: self.max_issues]

        return DigestEntry(
            timestamp=ts,
            ok_count=ok,
            warning_count=warning,
            critical_count=critical,
            avg_score=avg_score,
            top_issues=issues,
        )
