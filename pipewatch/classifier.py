"""Metric classifier — assigns severity classes to evaluations based on configurable rules."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pipewatch.metrics import MetricEvaluation, MetricStatus


@dataclass
class ClassificationRule:
    name: str
    status: MetricStatus
    min_value: Optional[float] = None
    max_value: Optional[float] = None

    def matches(self, evaluation: MetricEvaluation) -> bool:
        if evaluation.status != self.status:
            return False
        value = evaluation.metric.value
        if self.min_value is not None and value < self.min_value:
            return False
        if self.max_value is not None and value > self.max_value:
            return False
        return True

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status.value,
            "min_value": self.min_value,
            "max_value": self.max_value,
        }


@dataclass
class ClassificationResult:
    metric_name: str
    matched_class: Optional[str]
    status: MetricStatus
    value: float

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "matched_class": self.matched_class,
            "status": self.status.value,
            "value": self.value,
        }


class MetricClassifier:
    def __init__(self) -> None:
        self._rules: List[ClassificationRule] = []

    def add_rule(self, rule: ClassificationRule) -> ClassificationRule:
        self._rules.append(rule)
        return rule

    def classify(self, evaluation: MetricEvaluation) -> ClassificationResult:
        for rule in self._rules:
            if rule.matches(evaluation):
                return ClassificationResult(
                    metric_name=evaluation.metric.name,
                    matched_class=rule.name,
                    status=evaluation.status,
                    value=evaluation.metric.value,
                )
        return ClassificationResult(
            metric_name=evaluation.metric.name,
            matched_class=None,
            status=evaluation.status,
            value=evaluation.metric.value,
        )

    def classify_all(
        self, evaluations: List[MetricEvaluation]
    ) -> List[ClassificationResult]:
        return [self.classify(ev) for ev in evaluations]

    def rules(self) -> List[ClassificationRule]:
        return list(self._rules)
