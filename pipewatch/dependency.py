from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from pipewatch.metrics import MetricStatus


@dataclass
class DependencyNode:
    name: str
    depends_on: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"name": self.name, "depends_on": self.depends_on}


@dataclass
class DependencyViolation:
    metric: str
    blocked_by: str
    reason: str

    def to_dict(self) -> dict:
        return {"metric": self.metric, "blocked_by": self.blocked_by, "reason": self.reason}


class DependencyGraph:
    def __init__(self) -> None:
        self._nodes: Dict[str, DependencyNode] = {}

    def register(self, name: str, depends_on: Optional[List[str]] = None) -> None:
        self._nodes[name] = DependencyNode(name=name, depends_on=depends_on or [])

    def get_dependencies(self, name: str) -> List[str]:
        node = self._nodes.get(name)
        return node.depends_on if node else []

    def check_violations(
        self, statuses: Dict[str, MetricStatus]
    ) -> List[DependencyViolation]:
        violations: List[DependencyViolation] = []
        for name, node in self._nodes.items():
            current = statuses.get(name)
            if current is None:
                continue
            for dep in node.depends_on:
                dep_status = statuses.get(dep)
                if dep_status == MetricStatus.CRITICAL:
                    violations.append(
                        DependencyViolation(
                            metric=name,
                            blocked_by=dep,
                            reason=f"dependency '{dep}' is CRITICAL",
                        )
                    )
        return violations

    def topological_order(self) -> List[str]:
        visited: Set[str] = set()
        order: List[str] = []

        def visit(n: str) -> None:
            if n in visited:
                return
            visited.add(n)
            for dep in self._nodes.get(n, DependencyNode(n)).depends_on:
                visit(dep)
            order.append(n)

        for name in self._nodes:
            visit(name)
        return order
