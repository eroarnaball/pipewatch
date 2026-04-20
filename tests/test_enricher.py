"""Tests for pipewatch.enricher."""

import pytest
from pipewatch.metrics import MetricStatus, PipelineMetric, MetricEvaluation
from pipewatch.enricher import EnrichedEvaluation, MetricEnricher


def make_evaluation(name: str, value: float, status: MetricStatus) -> MetricEvaluation:
    m = PipelineMetric(name=name, value=value, unit="")
    return MetricEvaluation(metric=m, status=status)


def make_enricher() -> MetricEnricher:
    e = MetricEnricher()
    e.register("doubled", lambda ev: ev.metric.value * 2)
    e.register("is_ok", lambda ev: ev.status == MetricStatus.OK)
    return e


def test_enrich_adds_metadata():
    e = make_enricher()
    ev = make_evaluation("latency", 5.0, MetricStatus.OK)
    result = e.enrich(ev)
    assert isinstance(result, EnrichedEvaluation)
    assert result.get("doubled") == 10.0
    assert result.get("is_ok") is True


def test_enrich_critical_status():
    e = make_enricher()
    ev = make_evaluation("error_rate", 0.9, MetricStatus.CRITICAL)
    result = e.enrich(ev)
    assert result.get("is_ok") is False


def test_enrich_all_returns_correct_count():
    e = make_enricher()
    evs = [
        make_evaluation("a", 1.0, MetricStatus.OK),
        make_evaluation("b", 2.0, MetricStatus.WARNING),
        make_evaluation("c", 3.0, MetricStatus.CRITICAL),
    ]
    results = e.enrich_all(evs)
    assert len(results) == 3


def test_get_returns_default_for_missing_key():
    e = make_enricher()
    ev = make_evaluation("x", 0.0, MetricStatus.OK)
    result = e.enrich(ev)
    assert result.get("nonexistent", "fallback") == "fallback"


def test_to_dict_contains_expected_keys():
    e = make_enricher()
    ev = make_evaluation("row_count", 100.0, MetricStatus.WARNING)
    result = e.enrich(ev)
    d = result.to_dict()
    assert "metric" in d
    assert "value" in d
    assert "status" in d
    assert "doubled" in d
    assert "is_ok" in d


def test_rule_exception_sets_none():
    e = MetricEnricher()
    e.register("bad", lambda ev: 1 / 0)  # will raise ZeroDivisionError
    ev = make_evaluation("x", 1.0, MetricStatus.OK)
    result = e.enrich(ev)
    assert result.get("bad") is None


def test_no_rules_produces_empty_metadata():
    e = MetricEnricher()
    ev = make_evaluation("y", 42.0, MetricStatus.OK)
    result = e.enrich(ev)
    assert result.metadata == {}


def test_multiple_rules_all_applied():
    e = MetricEnricher()
    e.register("k1", lambda ev: "v1")
    e.register("k2", lambda ev: "v2")
    e.register("k3", lambda ev: "v3")
    ev = make_evaluation("z", 0.0, MetricStatus.OK)
    result = e.enrich(ev)
    assert result.get("k1") == "v1"
    assert result.get("k2") == "v2"
    assert result.get("k3") == "v3"
