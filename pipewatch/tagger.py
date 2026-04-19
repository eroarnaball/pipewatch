"""Metric tagging and filtering support."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class TaggedMetric:
    name: str
    tags: Dict[str, str] = field(default_factory=dict)

    def has_tag(self, key: str, value: Optional[str] = None) -> bool:
        if key not in self.tags:
            return False
        return value is None or self.tags[key] == value

    def to_dict(self) -> dict:
        return {"name": self.name, "tags": self.tags}


class MetricTagger:
    def __init__(self) -> None:
        self._registry: Dict[str, TaggedMetric] = {}

    def tag(self, name: str, tags: Dict[str, str]) -> TaggedMetric:
        if name not in self._registry:
            self._registry[name] = TaggedMetric(name=name)
        self._registry[name].tags.update(tags)
        return self._registry[name]

    def untag(self, name: str, keys: List[str]) -> None:
        if name in self._registry:
            for k in keys:
                self._registry[name].tags.pop(k, None)

    def get(self, name: str) -> Optional[TaggedMetric]:
        return self._registry.get(name)

    def filter_by_tag(self, key: str, value: Optional[str] = None) -> List[TaggedMetric]:
        return [
            m for m in self._registry.values()
            if m.has_tag(key, value)
        ]

    def all_tags(self) -> Set[str]:
        keys: Set[str] = set()
        for m in self._registry.values():
            keys.update(m.tags.keys())
        return keys

    def list_metrics(self) -> List[TaggedMetric]:
        return list(self._registry.values())
