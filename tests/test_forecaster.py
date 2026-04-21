"""Tests for pipewatch.forecaster."""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from pipewatch.forecaster import MetricForecaster, ForecastResult, _linear_regression
from pipewatch.history import MetricHistory, HistoryEntry
from pipewatch.metrics import MetricStatus, PipelineMetric, MetricEvaluation


def _make_entry(name: str, value: float, ts: datetime) -> HistoryEntry:
    metric = PipelineMetric(name=name, value=value)
    evaluation = MetricEvaluation(metric=metric, status=MetricStatus.OK)
    return HistoryEntry(evaluation=evaluation, timestamp=ts)


def make_history(name: str, values: list, start: datetime = None) -> MetricHistory:
    history = MetricHistory(max_entries=100)
    base = start or datetime(2024, 1, 1)
    for i, v in enumerate(values):
        entry = _make_entry(name, v, base + timedelta(minutes=i))
        history.record(name, entry)
    return history


# --- unit tests for _linear_regression ---

def test_linear_regression_flat():
    slope, intercept = _linear_regression([5.0, 5.0, 5.0, 5.0])
    assert slope == pytest.approx(0.0)
    assert intercept == pytest.approx(5.0)


def test_linear_regression_rising():
    slope, intercept = _linear_regression([0.0, 1.0, 2.0, 3.0])
    assert slope == pytest.approx(1.0)
    assert intercept == pytest.approx(0.0)


# --- MetricForecaster tests ---

def test_forecast_returns_none_when_insufficient_data():
    history = make_history("m", [1.0, 2.0])  # only 2 points, min is 3
    f = MetricForecaster(min_points=3)
    result = f.forecast(history, "m")
    assert result is None


def test_forecast_returns_result_with_enough_data():
    history = make_history("m", [1.0, 2.0, 3.0, 4.0, 5.0])
    f = MetricForecaster(min_points=3)
    result = f.forecast(history, "m")
    assert isinstance(result, ForecastResult)
    assert result.metric_name == "m"


def test_forecast_horizon_1_predicts_next_step():
    values = [float(i) for i in range(10)]  # 0..9, slope=1
    history = make_history("m", values)
    f = MetricForecaster(min_points=3)
    result = f.forecast(history, "m", horizon=1)
    assert result is not None
    assert result.predicted_value == pytest.approx(10.0, abs=0.01)


def test_forecast_horizon_affects_prediction():
    values = [float(i) for i in range(10)]
    history = make_history("m", values)
    f = MetricForecaster()
    r1 = f.forecast(history, "m", horizon=1)
    r5 = f.forecast(history, "m", horizon=5)
    assert r5.predicted_value > r1.predicted_value


def test_confidence_low_for_small_sample():
    history = make_history("m", [1.0, 2.0, 3.0, 4.0])
    f = MetricForecaster(min_points=3)
    result = f.forecast(history, "m")
    assert result.confidence == "low"


def test_confidence_medium_for_mid_sample():
    history = make_history("m", [float(i) for i in range(12)])
    f = MetricForecaster(min_points=3)
    result = f.forecast(history, "m")
    assert result.confidence == "medium"


def test_confidence_high_for_large_sample():
    history = make_history("m", [float(i) for i in range(25)])
    f = MetricForecaster(min_points=3)
    result = f.forecast(history, "m")
    assert result.confidence == "high"


def test_to_dict_has_expected_keys():
    history = make_history("m", [float(i) for i in range(10)])
    f = MetricForecaster(min_points=3)
    result = f.forecast(history, "m")
    d = result.to_dict()
    assert "metric_name" in d
    assert "predicted_value" in d
    assert "slope" in d
    assert "confidence" in d
    assert "horizon" in d


def test_forecast_unknown_metric_returns_none():
    history = MetricHistory(max_entries=50)
    f = MetricForecaster(min_points=3)
    result = f.forecast(history, "nonexistent")
    assert result is None
