"""Checkpoint tracking for pipeline stages.

Allows pipelines to register named checkpoints and tracks whether
each checkpoint was reached within an expected time window.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional


@dataclass
class CheckpointEntry:
    """A single checkpoint record for a named pipeline stage."""

    name: str
    reached_at: datetime
    expected_by: Optional[datetime] = None

    @property
    def is_late(self) -> bool:
        """Return True if the checkpoint was reached after the expected time."""
        if self.expected_by is None:
            return False
        return self.reached_at > self.expected_by

    @property
    def lateness_seconds(self) -> Optional[float]:
        """Return how many seconds late the checkpoint was, or None if on time."""
        if not self.is_late or self.expected_by is None:
            return None
        return (self.reached_at - self.expected_by).total_seconds()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "reached_at": self.reached_at.isoformat(),
            "expected_by": self.expected_by.isoformat() if self.expected_by else None,
            "is_late": self.is_late,
            "lateness_seconds": self.lateness_seconds,
        }


@dataclass
class MissedCheckpoint:
    """Represents a checkpoint that was expected but never reached."""

    name: str
    expected_by: datetime
    checked_at: datetime

    @property
    def overdue_seconds(self) -> float:
        return (self.checked_at - self.expected_by).total_seconds()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "expected_by": self.expected_by.isoformat(),
            "checked_at": self.checked_at.isoformat(),
            "overdue_seconds": self.overdue_seconds,
        }


class PipelineCheckpoint:
    """Tracks checkpoint completion for a named pipeline.

    Usage::

        cp = PipelineCheckpoint("etl_pipeline")
        cp.expect("extract", within_seconds=60)
        cp.mark("extract")
        result = cp.audit()
    """

    def __init__(self, pipeline_name: str) -> None:
        self.pipeline_name = pipeline_name
        self._entries: List[CheckpointEntry] = []
        self._expectations: Dict[str, timedelta] = {}
        self._start: datetime = datetime.utcnow()

    def expect(self, name: str, within_seconds: float) -> None:
        """Register an expectation that a checkpoint will be reached within a time window."""
        self._expectations[name] = timedelta(seconds=within_seconds)

    def mark(self, name: str, at: Optional[datetime] = None) -> CheckpointEntry:
        """Record that a checkpoint has been reached."""
        reached_at = at or datetime.utcnow()
        expected_by: Optional[datetime] = None
        if name in self._expectations:
            expected_by = self._start + self._expectations[name]
        entry = CheckpointEntry(name=name, reached_at=reached_at, expected_by=expected_by)
        self._entries.append(entry)
        return entry

    def audit(self, at: Optional[datetime] = None) -> "CheckpointAudit":
        """Audit the current checkpoint state and identify any missed checkpoints."""
        now = at or datetime.utcnow()
        reached_names = {e.name for e in self._entries}
        missed: List[MissedCheckpoint] = []
        for name, delta in self._expectations.items():
            if name not in reached_names:
                expected_by = self._start + delta
                if now > expected_by:
                    missed.append(MissedCheckpoint(
                        name=name,
                        expected_by=expected_by,
                        checked_at=now,
                    ))
        late = [e for e in self._entries if e.is_late]
        return CheckpointAudit(
            pipeline_name=self.pipeline_name,
            entries=list(self._entries),
            missed=missed,
            late=late,
        )

    def reset(self) -> None:
        """Clear all entries and reset the start time."""
        self._entries.clear()
        self._start = datetime.utcnow()


@dataclass
class CheckpointAudit:
    """Result of auditing a pipeline's checkpoints."""

    pipeline_name: str
    entries: List[CheckpointEntry]
    missed: List[MissedCheckpoint]
    late: List[CheckpointEntry]

    @property
    def has_issues(self) -> bool:
        return bool(self.missed or self.late)

    def to_dict(self) -> dict:
        return {
            "pipeline_name": self.pipeline_name,
            "reached": [e.to_dict() for e in self.entries],
            "missed": [m.to_dict() for m in self.missed],
            "late": [e.to_dict() for e in self.late],
            "has_issues": self.has_issues,
        }
