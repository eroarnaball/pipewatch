"""Tests for pipewatch.normalizer."""

import pytest
from pipewatch.normalizer import MetricNormalizer, NormalizationBounds, NormalizedValue


def make_normalizer() -> MetricNormalizer:
    n = MetricNormalizer()
    n.register("latency", min_value=0.0, max_value=1000.0)
    return n


def test_register_returns_bounds():
    n = MetricNormalizer()
    bounds = n.register("cpu", 0.0, 100.0)
    assert isinstance(bounds, NormalizationBounds)
    assert bounds.min_value == 0.0
    assert bounds.max_value == 100.0


def test_register_invalid_range_raises():
    n = MetricNormalizer()
    with pytest.raises(ValueError):
        n.register("bad", 100.0, 50.0)


def test_register_equal_range_raises():
    n = MetricNormalizer()
    with pytest.raises(ValueError):
        n.register("bad", 50.0, 50.0)


def test_normalize_returns_normalized_value():
    n = make_normalizer()
    result = n.normalize("latency", 500.0)
    assert isinstance(result, NormalizedValue)
    assert result.normalized == pytest.approx(0.5)


def test_normalize_min_value_gives_zero():
    n = make_normalizer()
    result = n.normalize("latency", 0.0)
    assert result.normalized == pytest.approx(0.0)


def test_normalize_max_value_gives_one():
    n = make_normalizer()
    result = n.normalize("latency", 1000.0)
    assert result.normalized == pytest.approx(1.0)


def test_normalize_clamps_below_min():
    n = make_normalizer()
    result = n.normalize("latency", -100.0)
    assert result.normalized == pytest.approx(0.0)


def test_normalize_clamps_above_max():
    n = make_normalizer()
    result = n.normalize("latency", 9999.0)
    assert result.normalized == pytest.approx(1.0)


def test_normalize_unknown_metric_returns_none():
    n = make_normalizer()
    assert n.normalize("unknown", 42.0) is None


def test_unregister_removes_metric():
    n = make_normalizer()
    assert n.unregister("latency") is True
    assert n.normalize("latency", 500.0) is None


def test_unregister_unknown_returns_false():
    n = MetricNormalizer()
    assert n.unregister("ghost") is False


def test_bounds_for_returns_correct_bounds():
    n = make_normalizer()
    b = n.bounds_for("latency")
    assert b is not None
    assert b.min_value == 0.0
    assert b.max_value == 1000.0


def test_bounds_for_unknown_returns_none():
    n = MetricNormalizer()
    assert n.bounds_for("missing") is None


def test_all_bounds_returns_all_registered():
    n = MetricNormalizer()
    n.register("a", 0.0, 10.0)
    n.register("b", 5.0, 50.0)
    all_b = n.all_bounds()
    assert set(all_b.keys()) == {"a", "b"}


def test_to_dict_has_expected_keys():
    n = make_normalizer()
    result = n.normalize("latency", 250.0)
    d = result.to_dict()
    assert "metric" in d
    assert "raw" in d
    assert "normalized" in d
    assert "bounds" in d
    assert "min" in d["bounds"]
    assert "max" in d["bounds"]
