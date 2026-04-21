"""Metric value sampler: periodically samples and stores recent values for a metric."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Deque, Dict, List, Optional


@dataclass
class Sample:
    metric_name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class SampleWindow:
    metric_name: str
    max_samples: int
    _samples: Deque[Sample] = field(default_factory=deque, init=False)

    def add(self, value: float) -> Sample:
        sample = Sample(metric_name=self.metric_name, value=value)
        self._samples.append(sample)
        if len(self._samples) > self.max_samples:
            self._samples.popleft()
        return sample

    @property
    def samples(self) -> List[Sample]:
        return list(self._samples)

    @property
    def values(self) -> List[float]:
        return [s.value for s in self._samples]

    def average(self) -> Optional[float]:
        if not self._samples:
            return None
        return sum(self.values) / len(self._samples)

    def latest(self) -> Optional[Sample]:
        return self._samples[-1] if self._samples else None

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "max_samples": self.max_samples,
            "count": len(self._samples),
            "average": self.average(),
            "samples": [s.to_dict() for s in self._samples],
        }


class MetricSampler:
    def __init__(self, default_max_samples: int = 60) -> None:
        self.default_max_samples = default_max_samples
        self._windows: Dict[str, SampleWindow] = {}

    def register(self, metric_name: str, max_samples: Optional[int] = None) -> SampleWindow:
        size = max_samples if max_samples is not None else self.default_max_samples
        window = SampleWindow(metric_name=metric_name, max_samples=size)
        self._windows[metric_name] = window
        return window

    def record(self, metric_name: str, value: float) -> Sample:
        if metric_name not in self._windows:
            self.register(metric_name)
        return self._windows[metric_name].add(value)

    def get_window(self, metric_name: str) -> Optional[SampleWindow]:
        return self._windows.get(metric_name)

    def all_windows(self) -> List[SampleWindow]:
        return list(self._windows.values())
