"""Snapshot: capture and restore pipeline metric state at a point in time."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from pipewatch.metrics import MetricStatus


@dataclass
class MetricSnapshot:
    name: str
    value: float
    status: MetricStatus
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "status": self.status.value,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MetricSnapshot":
        return cls(
            name=data["name"],
            value=data["value"],
            status=MetricStatus(data["status"]),
            timestamp=data["timestamp"],
        )


@dataclass
class PipelineSnapshot:
    captured_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metrics: list[MetricSnapshot] = field(default_factory=list)

    def add(self, snapshot: MetricSnapshot) -> None:
        self.metrics.append(snapshot)

    def to_dict(self) -> dict[str, Any]:
        return {
            "captured_at": self.captured_at,
            "metrics": [m.to_dict() for m in self.metrics],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PipelineSnapshot":
        snap = cls(captured_at=data["captured_at"])
        snap.metrics = [MetricSnapshot.from_dict(m) for m in data.get("metrics", [])]
        return snap

    @classmethod
    def from_json(cls, raw: str) -> "PipelineSnapshot":
        return cls.from_dict(json.loads(raw))

    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {s.value: 0 for s in MetricStatus}
        for m in self.metrics:
            counts[m.status.value] += 1
        return counts
