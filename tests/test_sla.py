import pytest
from datetime import datetime, timezone
from pipewatch.sla import SLAConfig, SLAResult, SLATracker
from pipewatch.history import MetricHistory, HistoryEntry
from pipewatch.metrics import MetricStatus, PipelineMetric, MetricEvaluation


def make_history(entries: list[tuple[str, MetricStatus]]) -> MetricHistory:
    history = MetricHistory()
    for name, status in entries:
        metric = PipelineMetric(name=name, value=1.0)
        evaluation = MetricEvaluation(metric=metric, status=status)
        history.record(name, HistoryEntry(evaluation=evaluation, timestamp=datetime.now(timezone.utc)))
    return history


def make_tracker(*configs: SLAConfig) -> SLATracker:
    tracker = SLATracker()
    for config in configs:
        tracker.register(config)
    return tracker


def test_evaluate_returns_none_for_unregistered_metric():
    tracker = make_tracker()
    history = make_history([("orders", MetricStatus.OK)])
    result = tracker.evaluate("orders", history)
    assert result is None


def test_evaluate_empty_history_returns_zero_ratios():
    tracker = make_tracker(SLAConfig("orders"))
    history = MetricHistory()
    result = tracker.evaluate("orders", history)
    assert result is not None
    assert result.critical_ratio == 0.0
    assert result.warning_ratio == 0.0
    assert result.total_entries == 0


def test_no_breach_when_all_ok():
    tracker = make_tracker(SLAConfig("orders", max_critical_ratio=0.05, max_warning_ratio=0.10))
    history = make_history([("orders", MetricStatus.OK)] * 10)
    result = tracker.evaluate("orders", history)
    assert result is not None
    assert not result.critical_breached
    assert not result.warning_breached
    assert not result.any_breached


def test_critical_breach_detected():
    tracker = make_tracker(SLAConfig("orders", max_critical_ratio=0.05))
    entries = [("orders", MetricStatus.OK)] * 8 + [("orders", MetricStatus.CRITICAL)] * 2
    history = make_history(entries)
    result = tracker.evaluate("orders", history)
    assert result is not None
    assert result.critical_ratio == pytest.approx(0.2)
    assert result.critical_breached is True


def test_warning_breach_detected():
    tracker = make_tracker(SLAConfig("orders", max_warning_ratio=0.05))
    entries = [("orders", MetricStatus.OK)] * 8 + [("orders", MetricStatus.WARNING)] * 2
    history = make_history(entries)
    result = tracker.evaluate("orders", history)
    assert result is not None
    assert result.warning_ratio == pytest.approx(0.2)
    assert result.warning_breached is True


def test_evaluate_all_returns_all_registered_metrics():
    tracker = make_tracker(
        SLAConfig("orders"),
        SLAConfig("payments"),
    )
    history = make_history([("orders", MetricStatus.OK), ("payments", MetricStatus.OK)])
    results = tracker.evaluate_all(history)
    assert "orders" in results
    assert "payments" in results


def test_to_dict_has_expected_keys():
    tracker = make_tracker(SLAConfig("orders"))
    history = make_history([("orders", MetricStatus.OK)])
    result = tracker.evaluate("orders", history)
    d = result.to_dict()
    expected_keys = {"metric_name", "critical_ratio", "warning_ratio", "critical_breached", "warning_breached", "total_entries", "any_breached"}
    assert expected_keys.issubset(d.keys())


def test_sla_config_to_dict():
    config = SLAConfig("orders", max_critical_ratio=0.01, max_warning_ratio=0.05)
    d = config.to_dict()
    assert d["metric_name"] == "orders"
    assert d["max_critical_ratio"] == 0.01
    assert d["max_warning_ratio"] == 0.05
