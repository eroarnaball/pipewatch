"""Cascade failure detection: identify chain reactions across dependent metrics."""

from dataclasses import dataclass, field
from typing import List, Optional
from pipewatch.metrics import MetricStatus, MetricEvaluation


@dataclass
class CascadeNode:
    metric_name: str
    status: MetricStatus
    triggered_by: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "status": self.status.value,
            "triggered_by": self.triggered_by,
        }


@dataclass
class CascadeResult:
    root_cause: str
    affected: List[CascadeNode] = field(default_factory=list)
    depth: int = 0

    def is_cascade(self) -> bool:
        return len(self.affected) > 1

    def to_dict(self) -> dict:
        return {
            "root_cause": self.root_cause,
            "depth": self.depth,
            "is_cascade": self.is_cascade(),
            "affected": [n.to_dict() for n in self.affected],
        }


class CascadeDetector:
    def __init__(self) -> None:
        self._dependencies: dict[str, List[str]] = {}

    def register_dependency(self, metric: str, depends_on: str) -> None:
        self._dependencies.setdefault(metric, []).append(depends_on)

    def detect(self, evaluations: List[MetricEvaluation]) -> Optional[CascadeResult]:
        status_map = {ev.metric.name: ev for ev in evaluations}
        non_ok = [
            ev for ev in evaluations if ev.status != MetricStatus.OK
        ]
        if not non_ok:
            return None

        # Find a root cause: a failing metric that no other failing metric depends on
        failing_names = {ev.metric.name for ev in non_ok}
        for ev in non_ok:
            deps = self._dependencies.get(ev.metric.name, [])
            upstream_failing = [d for d in deps if d in failing_names]
            if not upstream_failing:
                root = ev.metric.name
                affected = self._collect_affected(root, status_map, failing_names)
                if affected:
                    return CascadeResult(
                        root_cause=root,
                        affected=affected,
                        depth=self._max_depth(root, failing_names, set()),
                    )
        return None

    def _collect_affected(self, root: str, status_map: dict, failing: set) -> List[CascadeNode]:
        nodes = []
        for name in failing:
            deps = self._dependencies.get(name, [])
            triggered_by = root if root in deps else None
            ev = status_map.get(name)
            if ev:
                nodes.append(CascadeNode(
                    metric_name=name,
                    status=ev.status,
                    triggered_by=triggered_by,
                ))
        return nodes

    def _max_depth(self, root: str, failing: set, visited: set) -> int:
        if root in visited:
            return 0
        visited.add(root)
        children = [
            m for m, deps in self._dependencies.items()
            if root in deps and m in failing
        ]
        if not children:
            return 0
        return 1 + max(self._max_depth(c, failing, visited) for c in children)
