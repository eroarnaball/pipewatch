"""Metric filtering utilities for pipewatch.

Provides flexible filtering of metrics by status, tag, name pattern,
and other attributes for use in CLI output and programmatic queries.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from pipewatch.metrics import MetricEvaluation, MetricStatus


@dataclass
class MetricFilter:
    """Declarative filter criteria for metric evaluations."""

    statuses: Optional[List[MetricStatus]] = None
    name_pattern: Optional[str] = None  # supports shell-style wildcards
    tags: Optional[dict] = None  # key/value pairs that must all match
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    custom: List[Callable[[MetricEvaluation], bool]] = field(default_factory=list)

    def matches(self, evaluation: MetricEvaluation) -> bool:
        """Return True if the evaluation satisfies all filter criteria."""
        if self.statuses is not None and evaluation.status not in self.statuses:
            return False

        if self.name_pattern is not None:
            if not fnmatch.fnmatch(evaluation.metric.name, self.name_pattern):
                return False

        if self.min_value is not None and evaluation.metric.value is not None:
            if evaluation.metric.value < self.min_value:
                return False

        if self.max_value is not None and evaluation.metric.value is not None:
            if evaluation.metric.value > self.max_value:
                return False

        for fn in self.custom:
            if not fn(evaluation):
                return False

        return True


class EvaluationFilter:
    """Applies a MetricFilter to a collection of MetricEvaluation objects."""

    def __init__(self, criteria: MetricFilter) -> None:
        self.criteria = criteria

    def apply(self, evaluations: List[MetricEvaluation]) -> List[MetricEvaluation]:
        """Return only evaluations that match the filter criteria."""
        return [ev for ev in evaluations if self.criteria.matches(ev)]

    def first(self, evaluations: List[MetricEvaluation]) -> Optional[MetricEvaluation]:
        """Return the first matching evaluation, or None."""
        for ev in evaluations:
            if self.criteria.matches(ev):
                return ev
        return None


def filter_by_status(
    evaluations: List[MetricEvaluation], *statuses: MetricStatus
) -> List[MetricEvaluation]:
    """Convenience function to filter evaluations by one or more statuses."""
    criteria = MetricFilter(statuses=list(statuses))
    return EvaluationFilter(criteria).apply(evaluations)


def filter_by_pattern(
    evaluations: List[MetricEvaluation], pattern: str
) -> List[MetricEvaluation]:
    """Convenience function to filter evaluations by metric name pattern."""
    criteria = MetricFilter(name_pattern=pattern)
    return EvaluationFilter(criteria).apply(evaluations)
