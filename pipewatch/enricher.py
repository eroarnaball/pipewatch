"""Metric enrichment: attach computed metadata to evaluations."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pipewatch.metrics import MetricEvaluation, MetricStatus


@dataclass
class EnrichedEvaluation:
    """An evaluation decorated with additional computed metadata."""

    evaluation: MetricEvaluation
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.metadata.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        base = {
            "metric": self.evaluation.metric.name,
            "value": self.evaluation.metric.value,
            "status": self.evaluation.status.value,
        }
        base.update(self.metadata)
        return base


class EnrichmentRule:
    """A named rule that adds a metadata key to an evaluation."""

    def __init__(self, key: str, fn):
        self.key = key
        self.fn = fn

    def apply(self, evaluation: MetricEvaluation) -> Any:
        return self.fn(evaluation)


class MetricEnricher:
    """Applies a set of enrichment rules to produce EnrichedEvaluations."""

    def __init__(self):
        self._rules: List[EnrichmentRule] = []

    def register(self, key: str, fn) -> None:
        """Register a new enrichment rule."""
        self._rules.append(EnrichmentRule(key, fn))

    def enrich(self, evaluation: MetricEvaluation) -> EnrichedEvaluation:
        """Apply all rules to a single evaluation."""
        metadata: Dict[str, Any] = {}
        for rule in self._rules:
            try:
                metadata[rule.key] = rule.apply(evaluation)
            except Exception:
                metadata[rule.key] = None
        return EnrichedEvaluation(evaluation=evaluation, metadata=metadata)

    def enrich_all(
        self, evaluations: List[MetricEvaluation]
    ) -> List[EnrichedEvaluation]:
        """Enrich a list of evaluations."""
        return [self.enrich(ev) for ev in evaluations]
