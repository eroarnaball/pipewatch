"""Tests for pipewatch.inhibitor."""

import pytest
from pipewatch.inhibitor import AlertInhibitor, InhibitionRule, InhibitionResult


@pytest.fixture
def inhibitor() -> AlertInhibitor:
    return AlertInhibitor()


def test_add_rule_returns_rule(inhibitor):
    rule = inhibitor.add_rule("db_conn", ["query_latency", "write_throughput"])
    assert isinstance(rule, InhibitionRule)
    assert rule.source == "db_conn"
    assert "query_latency" in rule.targets


def test_not_inhibited_when_no_rules(inhibitor):
    result = inhibitor.is_inhibited("some_metric")
    assert isinstance(result, InhibitionResult)
    assert result.inhibited is False
    assert result.inhibited_by is None


def test_not_inhibited_when_source_not_firing(inhibitor):
    inhibitor.add_rule("db_conn", ["query_latency"])
    result = inhibitor.is_inhibited("query_latency")
    assert result.inhibited is False


def test_inhibited_when_source_is_firing(inhibitor):
    inhibitor.add_rule("db_conn", ["query_latency"])
    inhibitor.set_firing("db_conn")
    result = inhibitor.is_inhibited("query_latency")
    assert result.inhibited is True
    assert result.inhibited_by == "db_conn"


def test_clear_firing_removes_inhibition(inhibitor):
    inhibitor.add_rule("db_conn", ["query_latency"])
    inhibitor.set_firing("db_conn")
    inhibitor.clear_firing("db_conn")
    result = inhibitor.is_inhibited("query_latency")
    assert result.inhibited is False


def test_metric_not_in_targets_is_not_inhibited(inhibitor):
    inhibitor.add_rule("db_conn", ["query_latency"])
    inhibitor.set_firing("db_conn")
    result = inhibitor.is_inhibited("write_throughput")
    assert result.inhibited is False


def test_multiple_rules_first_matching_wins(inhibitor):
    inhibitor.add_rule("source_a", ["target_x"])
    inhibitor.add_rule("source_b", ["target_x"])
    inhibitor.set_firing("source_b")
    result = inhibitor.is_inhibited("target_x")
    assert result.inhibited is True
    assert result.inhibited_by == "source_b"


def test_active_sources_returns_firing_metrics(inhibitor):
    inhibitor.set_firing("db_conn")
    inhibitor.set_firing("cache")
    sources = inhibitor.active_sources()
    assert "db_conn" in sources
    assert "cache" in sources


def test_to_dict_has_expected_keys(inhibitor):
    rule = inhibitor.add_rule("db_conn", ["query_latency"], label="db-inhibit")
    d = rule.to_dict()
    assert d["source"] == "db_conn"
    assert d["targets"] == ["query_latency"]
    assert d["label"] == "db-inhibit"


def test_result_to_dict_inhibited(inhibitor):
    inhibitor.add_rule("db_conn", ["query_latency"])
    inhibitor.set_firing("db_conn")
    result = inhibitor.is_inhibited("query_latency")
    d = result.to_dict()
    assert d["inhibited"] is True
    assert d["inhibited_by"] == "db_conn"
    assert d["metric_name"] == "query_latency"
