"""Retention policy for metric history — prune entries older than a TTL."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from pipewatch.history import MetricHistory, HistoryEntry


@dataclass
class RetentionPolicy:
    """Defines how long history entries should be kept."""

    default_ttl_seconds: int = 86400  # 24 hours
    per_metric_ttl: Dict[str, int] = field(default_factory=dict)

    def ttl_for(self, metric_name: str) -> int:
        return self.per_metric_ttl.get(metric_name, self.default_ttl_seconds)

    def to_dict(self) -> dict:
        return {
            "default_ttl_seconds": self.default_ttl_seconds,
            "per_metric_ttl": dict(self.per_metric_ttl),
        }


@dataclass
class PruneResult:
    """Summary of a retention pruning operation."""

    metric_name: str
    removed: int
    remaining: int

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "removed": self.removed,
            "remaining": self.remaining,
        }


class RetentionManager:
    """Applies a RetentionPolicy to MetricHistory instances."""

    def __init__(self, policy: RetentionPolicy) -> None:
        self.policy = policy

    def prune(self, name: str, history: MetricHistory) -> PruneResult:
        """Remove entries older than the TTL for *name* from *history*."""
        ttl = self.policy.ttl_for(name)
        cutoff: datetime = datetime.utcnow() - timedelta(seconds=ttl)

        before = len(history.entries)
        history.entries = [
            e for e in history.entries if e.timestamp >= cutoff
        ]
        after = len(history.entries)

        return PruneResult(
            metric_name=name,
            removed=before - after,
            remaining=after,
        )

    def prune_all(
        self, histories: Dict[str, MetricHistory]
    ) -> List[PruneResult]:
        """Prune every history in the mapping and return per-metric results."""
        return [self.prune(name, hist) for name, hist in histories.items()]
