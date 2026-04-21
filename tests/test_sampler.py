"""Tests for pipewatch.sampler."""

import pytest
from pipewatch.sampler import MetricSampler, Sample, SampleWindow


def make_sampler(default_max: int = 5) -> MetricSampler:
    return MetricSampler(default_max_samples=default_max)


def test_record_creates_window_automatically():
    sampler = make_sampler()
    sample = sampler.record("cpu", 42.0)
    assert isinstance(sample, Sample)
    assert sample.metric_name == "cpu"
    assert sample.value == 42.0


def test_get_window_returns_none_for_unknown():
    sampler = make_sampler()
    assert sampler.get_window("missing") is None


def test_get_window_returns_window_after_record():
    sampler = make_sampler()
    sampler.record("mem", 70.0)
    window = sampler.get_window("mem")
    assert window is not None
    assert window.metric_name == "mem"


def test_max_samples_enforced():
    sampler = make_sampler(default_max=3)
    for i in range(6):
        sampler.record("cpu", float(i))
    window = sampler.get_window("cpu")
    assert len(window.samples) == 3
    assert window.values == [3.0, 4.0, 5.0]


def test_average_returns_correct_value():
    sampler = make_sampler()
    for v in [10.0, 20.0, 30.0]:
        sampler.record("latency", v)
    window = sampler.get_window("latency")
    assert window.average() == 20.0


def test_average_returns_none_for_empty_window():
    window = SampleWindow(metric_name="empty", max_samples=10)
    assert window.average() is None


def test_latest_returns_most_recent_sample():
    sampler = make_sampler()
    sampler.record("cpu", 1.0)
    sampler.record("cpu", 99.0)
    window = sampler.get_window("cpu")
    assert window.latest().value == 99.0


def test_latest_returns_none_for_empty_window():
    window = SampleWindow(metric_name="x", max_samples=5)
    assert window.latest() is None


def test_register_with_custom_max():
    sampler = make_sampler(default_max=10)
    sampler.register("disk", max_samples=2)
    for i in range(5):
        sampler.record("disk", float(i))
    window = sampler.get_window("disk")
    assert len(window.samples) == 2


def test_all_windows_returns_all_registered():
    sampler = make_sampler()
    sampler.record("a", 1.0)
    sampler.record("b", 2.0)
    names = {w.metric_name for w in sampler.all_windows()}
    assert names == {"a", "b"}


def test_sample_to_dict_has_expected_keys():
    sampler = make_sampler()
    sample = sampler.record("cpu", 55.5)
    d = sample.to_dict()
    assert set(d.keys()) == {"metric_name", "value", "timestamp"}
    assert d["metric_name"] == "cpu"
    assert d["value"] == 55.5


def test_window_to_dict_structure():
    sampler = make_sampler()
    sampler.record("net", 10.0)
    sampler.record("net", 20.0)
    d = sampler.get_window("net").to_dict()
    assert d["metric_name"] == "net"
    assert d["count"] == 2
    assert d["average"] == 15.0
    assert len(d["samples"]) == 2
