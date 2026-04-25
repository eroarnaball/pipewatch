"""Pipeline topology: map and visualize metric relationships."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class TopologyNode:
    name: str
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"name": self.name, "tags": self.tags}


@dataclass
class TopologyEdge:
    source: str
    target: str
    label: Optional[str] = None

    def to_dict(self) -> dict:
        return {"source": self.source, "target": self.target, "label": self.label}


class PipelineTopology:
    def __init__(self) -> None:
        self._nodes: Dict[str, TopologyNode] = {}
        self._edges: List[TopologyEdge] = []

    def add_node(self, name: str, tags: Optional[Dict[str, str]] = None) -> TopologyNode:
        node = TopologyNode(name=name, tags=tags or {})
        self._nodes[name] = node
        return node

    def add_edge(self, source: str, target: str, label: Optional[str] = None) -> TopologyEdge:
        edge = TopologyEdge(source=source, target=target, label=label)
        self._edges.append(edge)
        return edge

    def get_node(self, name: str) -> Optional[TopologyNode]:
        return self._nodes.get(name)

    def neighbors(self, name: str) -> List[str]:
        return [e.target for e in self._edges if e.source == name]

    def upstream(self, name: str) -> List[str]:
        return [e.source for e in self._edges if e.target == name]

    def all_nodes(self) -> List[TopologyNode]:
        return list(self._nodes.values())

    def all_edges(self) -> List[TopologyEdge]:
        return list(self._edges)

    def reachable_from(self, start: str) -> Set[str]:
        visited: Set[str] = set()
        stack = [start]
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            stack.extend(self.neighbors(current))
        visited.discard(start)
        return visited

    def to_dict(self) -> dict:
        return {
            "nodes": [n.to_dict() for n in self._nodes.values()],
            "edges": [e.to_dict() for e in self._edges],
        }
