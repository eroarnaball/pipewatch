import pytest
from datetime import datetime, timedelta
from pipewatch.quota import QuotaConfig, QuotaResult, QuotaTracker
from pipewatch.history import MetricHistory, HistoryEntry
from pipewatch.metrics import MetricStatus


def _make_entry(name: str, status: MetricStatus, offset_hours: int = 0) -> HistoryEntry:
    return HistoryEntry(
        metric_name=name,
        status=status,
        value=1.0,
        timestamp=datetime.utcnow() - timedelta(hours=offset_hours),
    )


def make_history(name: str, statuses: list) -> MetricHistory:
    h = MetricHistory(max_entries=200)
    for i, st in enumerate(statuses):
        h.record(_make_entry(name, st, offset_hours=len(statuses) - i))
    return h


def make_tracker(**kwargs) -> QuotaTracker:
    return QuotaTracker(default_config=QuotaConfig(**kwargs))


def test_evaluate_returns_none_for_empty_history():
    tracker = make_tracker()
    history = MetricHistory()
    result = tracker.evaluate("missing", history)
    assert result is None


def test_evaluate_all_ok_no_exceeded():
    tracker = make_tracker(max_warnings_pct=0.25, max_critical_pct=0.10)
    statuses = [MetricStatus.OK] * 10
    history = make_history("m", statuses)
    result = tracker.evaluate("m", history)
    assert result is not None
    assert result.warning_exceeded is False
    assert result.critical_exceeded is False
    assert result.any_exceeded is False


def test_evaluate_warning_exceeded():
    tracker = make_tracker(max_warnings_pct=0.20, max_critical_pct=0.10)
    statuses = [MetricStatus.WARNING] * 5 + [MetricStatus.OK] * 5
    history = make_history("m", statuses)
    result = tracker.evaluate("m", history)
    assert result is not None
    assert result.warning_pct == pytest.approx(0.5)
    assert result.warning_exceeded is True


def test_evaluate_critical_exceeded():
    tracker = make_tracker(max_warnings_pct=0.5, max_critical_pct=0.10)
    statuses = [MetricStatus.CRITICAL] * 3 + [MetricStatus.OK] * 7
    history = make_history("m", statuses)
    result = tracker.evaluate("m", history)
    assert result is not None
    assert result.critical_pct == pytest.approx(0.3)
    assert result.critical_exceeded is True


def test_per_metric_override_is_used():
    tracker = make_tracker(max_warnings_pct=0.5, max_critical_pct=0.5)
    tracker.register("strict", QuotaConfig(max_warnings_pct=0.05, max_critical_pct=0.01))
    statuses = [MetricStatus.WARNING] * 2 + [MetricStatus.OK] * 8
    history = make_history("strict", statuses)
    result = tracker.evaluate("strict", history)
    assert result is not None
    assert result.warning_exceeded is True


def test_to_dict_has_expected_keys():
    tracker = make_tracker()
    statuses = [MetricStatus.OK, MetricStatus.WARNING, MetricStatus.CRITICAL]
    history = make_history("pipe", statuses)
    result = tracker.evaluate("pipe", history)
    assert result is not None
    d = result.to_dict()
    for key in ("metric_name", "total", "warning_count", "critical_count",
                "warning_pct", "critical_pct", "warning_exceeded", "critical_exceeded"):
        assert key in d


def test_quota_config_to_dict():
    cfg = QuotaConfig(max_warnings_pct=0.15, max_critical_pct=0.05)
    d = cfg.to_dict()
    assert d["max_warnings_pct"] == 0.15
    assert d["max_critical_pct"] == 0.05
