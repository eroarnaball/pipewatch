"""Metric fingerprinting: generate stable hashes for alert deduplication and change detection."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Optional

from pipewatch.metrics import MetricEvaluation


@dataclass
class MetricFingerprint:
    metric_name: str
    status: str
    value: Optional[float]
    fingerprint: str

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "status": self.status,
            "value": self.value,
            "fingerprint": self.fingerprint,
        }


class FingerprintRegistry:
    """Tracks the last known fingerprint for each metric to detect changes."""

    def __init__(self) -> None:
        self._registry: dict[str, str] = {}

    def compute(self, evaluation: MetricEvaluation) -> MetricFingerprint:
        """Compute a stable fingerprint for the given evaluation."""
        payload = json.dumps(
            {
                "name": evaluation.metric.name,
                "status": evaluation.status.value,
                "value": evaluation.metric.value,
            },
            sort_keys=True,
        )
        digest = hashlib.sha256(payload.encode()).hexdigest()[:16]
        return MetricFingerprint(
            metric_name=evaluation.metric.name,
            status=evaluation.status.value,
            value=evaluation.metric.value,
            fingerprint=digest,
        )

    def has_changed(self, evaluation: MetricEvaluation) -> bool:
        """Return True if the fingerprint differs from the last recorded one."""
        fp = self.compute(evaluation)
        previous = self._registry.get(evaluation.metric.name)
        return previous != fp.fingerprint

    def record(self, evaluation: MetricEvaluation) -> MetricFingerprint:
        """Compute, store, and return the fingerprint for an evaluation."""
        fp = self.compute(evaluation)
        self._registry[evaluation.metric.name] = fp.fingerprint
        return fp

    def get(self, metric_name: str) -> Optional[str]:
        """Return the last recorded fingerprint for a metric, or None."""
        return self._registry.get(metric_name)

    def clear(self, metric_name: str) -> None:
        """Remove the stored fingerprint for a metric."""
        self._registry.pop(metric_name, None)
