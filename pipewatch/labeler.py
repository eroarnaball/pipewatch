"""Metric labeler: attach free-form key/value labels to pipeline metrics
and query metrics by label predicates."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class LabeledMetric:
    metric_name: str
    labels: Dict[str, str] = field(default_factory=dict)

    def get(self, key: str) -> Optional[str]:
        return self.labels.get(key)

    def set(self, key: str, value: str) -> None:
        self.labels[key] = value

    def remove(self, key: str) -> bool:
        if key in self.labels:
            del self.labels[key]
            return True
        return False

    def matches(self, key: str, value: Optional[str] = None) -> bool:
        if key not in self.labels:
            return False
        return value is None or self.labels[key] == value

    def to_dict(self) -> dict:
        return {"metric_name": self.metric_name, "labels": dict(self.labels)}


class MetricLabeler:
    def __init__(self) -> None:
        self._store: Dict[str, LabeledMetric] = {}

    def label(self, metric_name: str, key: str, value: str) -> LabeledMetric:
        if metric_name not in self._store:
            self._store[metric_name] = LabeledMetric(metric_name=metric_name)
        self._store[metric_name].set(key, value)
        return self._store[metric_name]

    def unlabel(self, metric_name: str, key: str) -> bool:
        entry = self._store.get(metric_name)
        if entry is None:
            return False
        return entry.remove(key)

    def get(self, metric_name: str) -> Optional[LabeledMetric]:
        return self._store.get(metric_name)

    def find(self, key: str, value: Optional[str] = None) -> List[LabeledMetric]:
        return [
            entry
            for entry in self._store.values()
            if entry.matches(key, value)
        ]

    def all_labels(self) -> Dict[str, List[str]]:
        result: Dict[str, List[str]] = {}
        for entry in self._store.values():
            for k, v in entry.labels.items():
                result.setdefault(k, [])
                if v not in result[k]:
                    result[k].append(v)
        return result

    def all_metrics(self) -> List[LabeledMetric]:
        return list(self._store.values())
