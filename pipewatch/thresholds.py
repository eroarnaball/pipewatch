"""Threshold evaluation logic for pipeline metrics."""
from typing import Optional
from pipewatch.metrics import MetricEvaluation, MetricStatus, PipelineMetric


class ThresholdEvaluator:
    """Evaluates a metric value against warning and critical thresholds."""

    def __init__(
        self,
        warning: Optional[float] = None,
        critical: Optional[float] = None,
        comparator: str = "gte",
    ):
        if comparator not in ("gte", "lte"):
            raise ValueError("comparator must be 'gte' or 'lte'")
        self.warning = warning
        self.critical = critical
        self.comparator = comparator

    def _exceeds(self, value: float, threshold: float) -> bool:
        if self.comparator == "gte":
            return value >= threshold
        return value <= threshold

    def evaluate(self, metric: PipelineMetric) -> MetricEvaluation:
        value = metric.value

        if self.critical is not None and self._exceeds(value, self.critical):
            status = MetricStatus.CRITICAL
            message = (
                f"{metric.metric_name}={value}{' ' + metric.unit if metric.unit else ''} "
                f"exceeds critical threshold {self.critical}"
            )
        elif self.warning is not None and self._exceeds(value, self.warning):
            status = MetricStatus.WARNING
            message = (
                f"{metric.metric_name}={value}{' ' + metric.unit if metric.unit else ''} "
                f"exceeds warning threshold {self.warning}"
            )
        else:
            status = MetricStatus.OK
            message = f"{metric.metric_name}={value} is within acceptable range"

        return MetricEvaluation(
            metric=metric,
            status=status,
            message=message,
            warning_threshold=self.warning,
            critical_threshold=self.critical,
        )
