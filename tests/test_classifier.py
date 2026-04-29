"""Tests for pipewatch.classifier."""
from __future__ import annotations
import pytest
from pipewatch.classifier import ClassificationRule, MetricClassifier
from pipewatch.metrics import MetricEvaluation, MetricStatus, PipelineMetric


def make_evaluation(name: str, value: float, status: MetricStatus) -> MetricEvaluation:
    return MetricEvaluation(
        metric=PipelineMetric(name=name, value=value),
        status=status,
    )


def make_classifier() -> MetricClassifier:
    clf = MetricClassifier()
    clf.add_rule(ClassificationRule("low-warn", MetricStatus.WARNING, min_value=0.0, max_value=50.0))
    clf.add_rule(ClassificationRule("high-warn", MetricStatus.WARNING, min_value=50.0))
    clf.add_rule(ClassificationRule("critical", MetricStatus.CRITICAL))
    return clf


def test_add_rule_returns_rule():
    clf = MetricClassifier()
    rule = clf.add_rule(ClassificationRule("test", MetricStatus.WARNING))
    assert rule.name == "test"


def test_rules_list_grows_with_additions():
    clf = MetricClassifier()
    assert len(clf.rules()) == 0
    clf.add_rule(ClassificationRule("r1", MetricStatus.WARNING))
    clf.add_rule(ClassificationRule("r2", MetricStatus.CRITICAL))
    assert len(clf.rules()) == 2


def test_classify_ok_returns_unclassified():
    clf = make_classifier()
    ev = make_evaluation("m", 10.0, MetricStatus.OK)
    result = clf.classify(ev)
    assert result.matched_class is None
    assert result.status == MetricStatus.OK


def test_classify_warning_low_value_matches_low_warn():
    clf = make_classifier()
    ev = make_evaluation("m", 30.0, MetricStatus.WARNING)
    result = clf.classify(ev)
    assert result.matched_class == "low-warn"


def test_classify_warning_high_value_matches_high_warn():
    clf = make_classifier()
    ev = make_evaluation("m", 80.0, MetricStatus.WARNING)
    result = clf.classify(ev)
    assert result.matched_class == "high-warn"


def test_classify_critical_matches_critical_rule():
    clf = make_classifier()
    ev = make_evaluation("m", 5.0, MetricStatus.CRITICAL)
    result = clf.classify(ev)
    assert result.matched_class == "critical"


def test_classify_all_returns_correct_count():
    clf = make_classifier()
    evs = [
        make_evaluation("a", 10.0, MetricStatus.OK),
        make_evaluation("b", 20.0, MetricStatus.WARNING),
        make_evaluation("c", 5.0, MetricStatus.CRITICAL),
    ]
    results = clf.classify_all(evs)
    assert len(results) == 3


def test_classification_result_to_dict_has_expected_keys():
    clf = make_classifier()
    ev = make_evaluation("latency", 30.0, MetricStatus.WARNING)
    result = clf.classify(ev)
    d = result.to_dict()
    assert "metric_name" in d
    assert "matched_class" in d
    assert "status" in d
    assert "value" in d


def test_rule_to_dict_has_expected_keys():
    rule = ClassificationRule("test", MetricStatus.WARNING, min_value=0.0, max_value=100.0)
    d = rule.to_dict()
    assert d["name"] == "test"
    assert d["status"] == MetricStatus.WARNING.value
    assert d["min_value"] == 0.0
    assert d["max_value"] == 100.0


def test_rule_with_no_value_bounds_matches_any_value():
    rule = ClassificationRule("any-critical", MetricStatus.CRITICAL)
    ev = make_evaluation("m", 999.0, MetricStatus.CRITICAL)
    assert rule.matches(ev) is True


def test_rule_does_not_match_wrong_status():
    rule = ClassificationRule("warn-rule", MetricStatus.WARNING, min_value=0.0)
    ev = make_evaluation("m", 50.0, MetricStatus.OK)
    assert rule.matches(ev) is False
