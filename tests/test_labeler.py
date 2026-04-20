"""Tests for pipewatch.labeler."""

import pytest
from pipewatch.labeler import LabeledMetric, MetricLabeler


def make_labeler() -> MetricLabeler:
    labeler = MetricLabeler()
    labeler.label("orders.latency", "env", "prod")
    labeler.label("orders.latency", "team", "backend")
    labeler.label("payments.errors", "env", "prod")
    labeler.label("payments.errors", "team", "payments")
    labeler.label("inventory.lag", "env", "staging")
    return labeler


def test_label_creates_entry():
    labeler = MetricLabeler()
    entry = labeler.label("my.metric", "env", "prod")
    assert entry.metric_name == "my.metric"
    assert entry.get("env") == "prod"


def test_label_updates_existing():
    labeler = MetricLabeler()
    labeler.label("my.metric", "env", "staging")
    labeler.label("my.metric", "env", "prod")
    assert labeler.get("my.metric").get("env") == "prod"


def test_get_returns_none_for_unknown():
    labeler = MetricLabeler()
    assert labeler.get("nonexistent") is None


def test_unlabel_removes_key():
    labeler = make_labeler()
    removed = labeler.unlabel("orders.latency", "team")
    assert removed is True
    assert labeler.get("orders.latency").get("team") is None


def test_unlabel_returns_false_for_missing_key():
    labeler = make_labeler()
    assert labeler.unlabel("orders.latency", "nonexistent") is False


def test_unlabel_returns_false_for_unknown_metric():
    labeler = MetricLabeler()
    assert labeler.unlabel("ghost.metric", "env") is False


def test_find_by_key_only():
    labeler = make_labeler()
    results = labeler.find("env")
    names = {r.metric_name for r in results}
    assert names == {"orders.latency", "payments.errors", "inventory.lag"}


def test_find_by_key_and_value():
    labeler = make_labeler()
    results = labeler.find("env", "prod")
    names = {r.metric_name for r in results}
    assert names == {"orders.latency", "payments.errors"}


def test_find_returns_empty_when_no_match():
    labeler = make_labeler()
    assert labeler.find("region") == []


def test_all_labels_aggregates_keys():
    labeler = make_labeler()
    labels = labeler.all_labels()
    assert "env" in labels
    assert set(labels["env"]) == {"prod", "staging"}
    assert "team" in labels


def test_all_metrics_returns_all():
    labeler = make_labeler()
    assert len(labeler.all_metrics()) == 3


def test_labeled_metric_to_dict():
    entry = LabeledMetric(metric_name="x", labels={"env": "prod"})
    d = entry.to_dict()
    assert d["metric_name"] == "x"
    assert d["labels"] == {"env": "prod"}


def test_matches_key_only_true_when_key_present():
    entry = LabeledMetric(metric_name="x", labels={"env": "prod"})
    assert entry.matches("env") is True


def test_matches_key_only_false_when_key_absent():
    entry = LabeledMetric(metric_name="x", labels={})
    assert entry.matches("env") is False
