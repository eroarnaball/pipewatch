"""Metric value normalization — scales raw metric values to a [0, 1] range
based on registered min/max bounds for each metric."""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class NormalizationBounds:
    min_value: float
    max_value: float

    def to_dict(self) -> dict:
        return {"min": self.min_value, "max": self.max_value}


@dataclass
class NormalizedValue:
    metric_name: str
    raw: float
    normalized: float
    bounds: NormalizationBounds

    def to_dict(self) -> dict:
        return {
            "metric": self.metric_name,
            "raw": self.raw,
            "normalized": round(self.normalized, 6),
            "bounds": self.bounds.to_dict(),
        }


class MetricNormalizer:
    def __init__(self) -> None:
        self._bounds: Dict[str, NormalizationBounds] = {}

    def register(self, metric_name: str, min_value: float, max_value: float) -> NormalizationBounds:
        if max_value <= min_value:
            raise ValueError("max_value must be greater than min_value")
        bounds = NormalizationBounds(min_value=min_value, max_value=max_value)
        self._bounds[metric_name] = bounds
        return bounds

    def unregister(self, metric_name: str) -> bool:
        if metric_name in self._bounds:
            del self._bounds[metric_name]
            return True
        return False

    def normalize(self, metric_name: str, value: float) -> Optional[NormalizedValue]:
        bounds = self._bounds.get(metric_name)
        if bounds is None:
            return None
        span = bounds.max_value - bounds.min_value
        normalized = (value - bounds.min_value) / span
        normalized = max(0.0, min(1.0, normalized))
        return NormalizedValue(
            metric_name=metric_name,
            raw=value,
            normalized=normalized,
            bounds=bounds,
        )

    def bounds_for(self, metric_name: str) -> Optional[NormalizationBounds]:
        return self._bounds.get(metric_name)

    def all_bounds(self) -> Dict[str, NormalizationBounds]:
        return dict(self._bounds)
