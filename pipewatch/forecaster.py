"""Simple linear trend forecasting for pipeline metrics."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.history import MetricHistory


@dataclass
class ForecastResult:
    metric_name: str
    horizon: int  # steps ahead
    predicted_value: float
    slope: float
    intercept: float
    confidence: str  # 'low' | 'medium' | 'high'

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "horizon": self.horizon,
            "predicted_value": round(self.predicted_value, 4),
            "slope": round(self.slope, 6),
            "intercept": round(self.intercept, 4),
            "confidence": self.confidence,
        }


MIN_POINTS_LOW = 3
MIN_POINTS_MEDIUM = 8
MIN_POINTS_HIGH = 20


def _linear_regression(values: List[float]):
    """Return (slope, intercept) via ordinary least squares."""
    n = len(values)
    xs = list(range(n))
    mean_x = sum(xs) / n
    mean_y = sum(values) / n
    ss_xx = sum((x - mean_x) ** 2 for x in xs)
    ss_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, values))
    slope = ss_xy / ss_xx if ss_xx != 0 else 0.0
    intercept = mean_y - slope * mean_x
    return slope, intercept


class MetricForecaster:
    """Forecast future metric values using linear regression over history."""

    def __init__(self, min_points: int = MIN_POINTS_LOW) -> None:
        self.min_points = min_points

    def forecast(
        self,
        history: MetricHistory,
        metric_name: str,
        horizon: int = 1,
    ) -> Optional[ForecastResult]:
        entries = history.get_all(metric_name)
        values = [
            e.evaluation.metric.value
            for e in entries
            if e.evaluation.metric.value is not None
        ]
        if len(values) < self.min_points:
            return None

        slope, intercept = _linear_regression(values)
        next_x = len(values) - 1 + horizon
        predicted = slope * next_x + intercept

        n = len(values)
        if n >= MIN_POINTS_HIGH:
            confidence = "high"
        elif n >= MIN_POINTS_MEDIUM:
            confidence = "medium"
        else:
            confidence = "low"

        return ForecastResult(
            metric_name=metric_name,
            horizon=horizon,
            predicted_value=predicted,
            slope=slope,
            intercept=intercept,
            confidence=confidence,
        )
