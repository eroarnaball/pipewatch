"""pipewatch/patch.py

Provides a MetricPatcher for applying runtime overrides to metric values
or statuses — useful for testing alert flows, simulating failures, or
temporarily suppressing noisy metrics by injecting a known-good value.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional

from pipewatch.metrics import MetricEvaluation, MetricStatus, PipelineMetric


@dataclass
class PatchEntry:
    """A single active patch override for a named metric."""

    metric_name: str
    override_value: Optional[float]
    override_status: Optional[MetricStatus]
    reason: str
    applied_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None

    def is_active(self) -> bool:
        """Return True if the patch is still within its validity window."""
        if self.expires_at is None:
            return True
        return datetime.now(timezone.utc) < self.expires_at

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "override_value": self.override_value,
            "override_status": self.override_status.value if self.override_status else None,
            "reason": self.reason,
            "applied_at": self.applied_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active(),
        }


class MetricPatcher:
    """Registry of runtime patches that can override metric evaluations.

    Patches are applied by name; expired patches are ignored and lazily
    removed on the next access.
    """

    def __init__(self) -> None:
        self._patches: Dict[str, PatchEntry] = {}

    def patch(
        self,
        metric_name: str,
        *,
        override_value: Optional[float] = None,
        override_status: Optional[MetricStatus] = None,
        reason: str = "",
        expires_at: Optional[datetime] = None,
    ) -> PatchEntry:
        """Register or replace a patch for *metric_name*."""
        entry = PatchEntry(
            metric_name=metric_name,
            override_value=override_value,
            override_status=override_status,
            reason=reason,
            expires_at=expires_at,
        )
        self._patches[metric_name] = entry
        return entry

    def remove(self, metric_name: str) -> bool:
        """Explicitly remove a patch. Returns True if a patch existed."""
        return self._patches.pop(metric_name, None) is not None

    def get(self, metric_name: str) -> Optional[PatchEntry]:
        """Return the active patch for *metric_name*, or None."""
        entry = self._patches.get(metric_name)
        if entry is None:
            return None
        if not entry.is_active():
            del self._patches[metric_name]
            return None
        return entry

    def apply(self, evaluation: MetricEvaluation) -> MetricEvaluation:
        """Return a (possibly patched) copy of *evaluation*.

        If no active patch exists the original object is returned unchanged.
        """
        name = evaluation.metric.name
        entry = self.get(name)
        if entry is None:
            return evaluation

        new_value = entry.override_value if entry.override_value is not None else evaluation.metric.value
        new_status = entry.override_status if entry.override_status is not None else evaluation.status

        patched_metric = PipelineMetric(
            name=evaluation.metric.name,
            value=new_value,
            unit=evaluation.metric.unit,
            description=evaluation.metric.description,
        )
        return MetricEvaluation(metric=patched_metric, status=new_status)

    def active_patches(self) -> Dict[str, PatchEntry]:
        """Return a snapshot of all currently active patches."""
        # Prune expired entries while we iterate.
        expired = [k for k, v in self._patches.items() if not v.is_active()]
        for k in expired:
            del self._patches[k]
        return dict(self._patches)
