"""Tests for pipewatch.budget module."""
import pytest
from datetime import datetime, timedelta
from pipewatch.budget import BudgetConfig, BudgetResult, ErrorBudgetTracker
from pipewatch.history import MetricHistory, HistoryEntry
from pipewatch.metrics import MetricStatus


def make_history(statuses):
    history = MetricHistory(metric_name="latency", max_entries=100)
    base = datetime(2024, 1, 1, 12, 0, 0)
    for i, status in enumerate(statuses):
        entry = HistoryEntry(
            timestamp=base + timedelta(minutes=i),
            value=float(i),
            status=status,
        )
        history.entries.append(entry)
    return history


def make_tracker(window=10, crit=0.1, warn=0.2):
    tracker = ErrorBudgetTracker()
    tracker.register(BudgetConfig(
        metric_name="latency",
        window_size=window,
        allowed_critical_ratio=crit,
        allowed_warning_ratio=warn,
    ))
    return tracker


def test_evaluate_returns_none_for_unregistered_metric():
    tracker = ErrorBudgetTracker()
    history = make_history([MetricStatus.OK])
    result = tracker.evaluate("unknown", history)
    assert result is None


def test_evaluate_empty_history_returns_zero_ratios():
    tracker = make_tracker()
    history = MetricHistory(metric_name="latency", max_entries=100)
    result = tracker.evaluate("latency", history)
    assert result is not None
    assert result.critical_ratio == 0.0
    assert result.warning_ratio == 0.0
    assert result.critical_budget_exceeded is False
    assert result.warning_budget_exceeded is False


def test_no_budget_exceeded_when_all_ok():
    tracker = make_tracker(window=5, crit=0.1, warn=0.2)
    history = make_history([MetricStatus.OK] * 5)
    result = tracker.evaluate("latency", history)
    assert result.critical_budget_exceeded is False
    assert result.warning_budget_exceeded is False
    assert result.any_exceeded is False


def test_critical_budget_exceeded():
    tracker = make_tracker(window=10, crit=0.1, warn=0.5)
    statuses = [MetricStatus.CRITICAL] * 3 + [MetricStatus.OK] * 7
    history = make_history(statuses)
    result = tracker.evaluate("latency", history)
    assert result.critical_ratio == pytest.approx(0.3)
    assert result.critical_budget_exceeded is True


def test_warning_budget_exceeded():
    tracker = make_tracker(window=10, crit=0.5, warn=0.1)
    statuses = [MetricStatus.WARNING] * 4 + [MetricStatus.OK] * 6
    history = make_history(statuses)
    result = tracker.evaluate("latency", history)
    assert result.warning_ratio == pytest.approx(0.4)
    assert result.warning_budget_exceeded is True


def test_window_size_limits_entries_considered():
    tracker = make_tracker(window=3, crit=0.1, warn=0.5)
    # 7 OKs then 3 CRITICALs — only last 3 in window
    statuses = [MetricStatus.OK] * 7 + [MetricStatus.CRITICAL] * 3
    history = make_history(statuses)
    result = tracker.evaluate("latency", history)
    assert result.window_size == 3
    assert result.critical_ratio == pytest.approx(1.0)
    assert result.critical_budget_exceeded is True


def test_to_dict_has_expected_keys():
    tracker = make_tracker(window=5, crit=0.1, warn=0.2)
    history = make_history([MetricStatus.OK] * 5)
    result = tracker.evaluate("latency", history)
    d = result.to_dict()
    for key in ("metric_name", "window_size", "critical_ratio", "warning_ratio",
                "allowed_critical_ratio", "allowed_warning_ratio",
                "critical_budget_exceeded", "warning_budget_exceeded"):
        assert key in d


def test_budget_config_to_dict():
    config = BudgetConfig(metric_name="latency", window_size=10,
                          allowed_critical_ratio=0.05, allowed_warning_ratio=0.15)
    d = config.to_dict()
    assert d["metric_name"] == "latency"
    assert d["window_size"] == 10
