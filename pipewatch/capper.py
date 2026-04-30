"""Alert value capper — clamps reported metric values to configured bounds before evaluation."""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class CapBounds:
    min_value: Optional[float]
    max_value: Optional[float]

    def to_dict(self) -> dict:
        return {"min_value": self.min_value, "max_value": self.max_value}


@dataclass
class CappedValue:
    metric_name: str
    original: float
    capped: float
    was_capped: bool

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "original": self.original,
            "capped": self.capped,
            "was_capped": self.was_capped,
        }


class MetricCapper:
    """Clamps metric values to registered min/max bounds."""

    def __init__(self) -> None:
        self._bounds: Dict[str, CapBounds] = {}

    def register(self, name: str, min_value: Optional[float] = None, max_value: Optional[float] = None) -> CapBounds:
        if min_value is not None and max_value is not None and min_value > max_value:
            raise ValueError(f"min_value {min_value} must not exceed max_value {max_value}")
        bounds = CapBounds(min_value=min_value, max_value=max_value)
        self._bounds[name] = bounds
        return bounds

    def get_bounds(self, name: str) -> Optional[CapBounds]:
        return self._bounds.get(name)

    def cap(self, name: str, value: float) -> CappedValue:
        bounds = self._bounds.get(name)
        if bounds is None:
            return CappedValue(metric_name=name, original=value, capped=value, was_capped=False)
        capped = value
        if bounds.min_value is not None:
            capped = max(capped, bounds.min_value)
        if bounds.max_value is not None:
            capped = min(capped, bounds.max_value)
        return CappedValue(metric_name=name, original=value, capped=capped, was_capped=(capped != value))

    def all_bounds(self) -> Dict[str, CapBounds]:
        return dict(self._bounds)
