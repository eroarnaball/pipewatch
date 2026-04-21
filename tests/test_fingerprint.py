"""Tests for pipewatch.fingerprint."""

from __future__ import annotations

import pytest

from pipewatch.metrics import MetricEvaluation, MetricStatus, PipelineMetric
from pipewatch.fingerprint import FingerprintRegistry, MetricFingerprint


def make_evaluation(
    name: str = "latency",
    value: float = 1.0,
    status: MetricStatus = MetricStatus.OK,
) -> MetricEvaluation:
    metric = PipelineMetric(name=name, value=value)
    return MetricEvaluation(metric=metric, status=status)


def make_registry() -> FingerprintRegistry:
    return FingerprintRegistry()


def test_compute_returns_fingerprint_object():
    reg = make_registry()
    ev = make_evaluation()
    fp = reg.compute(ev)
    assert isinstance(fp, MetricFingerprint)
    assert fp.metric_name == "latency"
    assert fp.status == MetricStatus.OK.value
    assert fp.value == 1.0
    assert len(fp.fingerprint) == 16


def test_same_evaluation_produces_same_fingerprint():
    reg = make_registry()
    ev = make_evaluation(value=5.0, status=MetricStatus.WARNING)
    fp1 = reg.compute(ev)
    fp2 = reg.compute(ev)
    assert fp1.fingerprint == fp2.fingerprint


def test_different_status_produces_different_fingerprint():
    reg = make_registry()
    ev_ok = make_evaluation(status=MetricStatus.OK)
    ev_crit = make_evaluation(status=MetricStatus.CRITICAL)
    assert reg.compute(ev_ok).fingerprint != reg.compute(ev_crit).fingerprint


def test_different_value_produces_different_fingerprint():
    reg = make_registry()
    ev1 = make_evaluation(value=1.0)
    ev2 = make_evaluation(value=99.0)
    assert reg.compute(ev1).fingerprint != reg.compute(ev2).fingerprint


def test_has_changed_true_before_first_record():
    reg = make_registry()
    ev = make_evaluation()
    assert reg.has_changed(ev) is True


def test_has_changed_false_after_record():
    reg = make_registry()
    ev = make_evaluation()
    reg.record(ev)
    assert reg.has_changed(ev) is False


def test_has_changed_true_after_status_change():
    reg = make_registry()
    ev_ok = make_evaluation(status=MetricStatus.OK)
    reg.record(ev_ok)
    ev_warn = make_evaluation(status=MetricStatus.WARNING)
    assert reg.has_changed(ev_warn) is True


def test_get_returns_none_before_record():
    reg = make_registry()
    assert reg.get("unknown") is None


def test_get_returns_fingerprint_after_record():
    reg = make_registry()
    ev = make_evaluation()
    fp = reg.record(ev)
    assert reg.get("latency") == fp.fingerprint


def test_clear_removes_entry():
    reg = make_registry()
    ev = make_evaluation()
    reg.record(ev)
    reg.clear("latency")
    assert reg.get("latency") is None
    assert reg.has_changed(ev) is True


def test_to_dict_has_expected_keys():
    reg = make_registry()
    ev = make_evaluation()
    fp = reg.compute(ev)
    d = fp.to_dict()
    assert set(d.keys()) == {"metric_name", "status", "value", "fingerprint"}
