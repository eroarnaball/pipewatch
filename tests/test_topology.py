"""Tests for pipewatch.topology."""
import pytest
from pipewatch.topology import PipelineTopology, TopologyNode, TopologyEdge


def make_topology() -> PipelineTopology:
    topo = PipelineTopology()
    topo.add_node("a", tags={"env": "prod"})
    topo.add_node("b")
    topo.add_node("c")
    topo.add_edge("a", "b", label="step1")
    topo.add_edge("b", "c", label="step2")
    return topo


def test_add_node_returns_node():
    topo = PipelineTopology()
    node = topo.add_node("x", tags={"k": "v"})
    assert isinstance(node, TopologyNode)
    assert node.name == "x"
    assert node.tags == {"k": "v"}


def test_get_node_returns_correct_node():
    topo = make_topology()
    node = topo.get_node("a")
    assert node is not None
    assert node.name == "a"
    assert node.tags == {"env": "prod"}


def test_get_node_returns_none_for_unknown():
    topo = make_topology()
    assert topo.get_node("z") is None


def test_add_edge_returns_edge():
    topo = PipelineTopology()
    topo.add_node("x")
    topo.add_node("y")
    edge = topo.add_edge("x", "y", label="link")
    assert isinstance(edge, TopologyEdge)
    assert edge.source == "x"
    assert edge.target == "y"
    assert edge.label == "link"


def test_neighbors_returns_downstream():
    topo = make_topology()
    assert topo.neighbors("a") == ["b"]
    assert topo.neighbors("b") == ["c"]
    assert topo.neighbors("c") == []


def test_upstream_returns_sources():
    topo = make_topology()
    assert topo.upstream("b") == ["a"]
    assert topo.upstream("a") == []


def test_reachable_from_includes_transitive():
    topo = make_topology()
    reachable = topo.reachable_from("a")
    assert "b" in reachable
    assert "c" in reachable
    assert "a" not in reachable


def test_reachable_from_leaf_is_empty():
    topo = make_topology()
    assert topo.reachable_from("c") == set()


def test_all_nodes_returns_all():
    topo = make_topology()
    names = {n.name for n in topo.all_nodes()}
    assert names == {"a", "b", "c"}


def test_all_edges_returns_all():
    topo = make_topology()
    assert len(topo.all_edges()) == 2


def test_to_dict_has_nodes_and_edges():
    topo = make_topology()
    d = topo.to_dict()
    assert "nodes" in d
    assert "edges" in d
    assert len(d["nodes"]) == 3
    assert len(d["edges"]) == 2


def test_node_to_dict_has_expected_keys():
    node = TopologyNode(name="m", tags={"x": "1"})
    d = node.to_dict()
    assert d["name"] == "m"
    assert d["tags"] == {"x": "1"}


def test_edge_to_dict_has_expected_keys():
    edge = TopologyEdge(source="a", target="b", label="lbl")
    d = edge.to_dict()
    assert d["source"] == "a"
    assert d["target"] == "b"
    assert d["label"] == "lbl"
