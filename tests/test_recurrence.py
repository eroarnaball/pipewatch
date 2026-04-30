import pytest

from pipewatch.metrics import MetricStatus
from pipewatch.recurrence import RecurrenceTracker, RecurrenceEntry, RecurrenceResult


def make_tracker(threshold: int = 3) -> RecurrenceTracker:
    return RecurrenceTracker(threshold=threshold)


def test_ok_status_does_not_create_entry():
    tracker = make_tracker()
    result = tracker.record("cpu", MetricStatus.OK)
    assert result.count == 0
    assert result.is_recurring is False
    assert tracker.get_entry("cpu") is None


def test_single_warning_is_not_recurring():
    tracker = make_tracker(threshold=3)
    result = tracker.record("cpu", MetricStatus.WARNING)
    assert result.count == 1
    assert result.is_recurring is False


def test_repeated_warning_reaches_threshold():
    tracker = make_tracker(threshold=3)
    for _ in range(2):
        tracker.record("cpu", MetricStatus.WARNING)
    result = tracker.record("cpu", MetricStatus.WARNING)
    assert result.count == 3
    assert result.is_recurring is True


def test_count_increments_correctly():
    tracker = make_tracker(threshold=5)
    for i in range(4):
        result = tracker.record("db.latency", MetricStatus.CRITICAL)
    assert result.count == 4
    assert result.is_recurring is False
    result = tracker.record("db.latency", MetricStatus.CRITICAL)
    assert result.count == 5
    assert result.is_recurring is True


def test_status_change_resets_count():
    tracker = make_tracker(threshold=3)
    for _ in range(3):
        tracker.record("cpu", MetricStatus.WARNING)
    # status changes to CRITICAL — resets count
    result = tracker.record("cpu", MetricStatus.CRITICAL)
    assert result.count == 1
    assert result.is_recurring is False


def test_ok_clears_existing_entry():
    tracker = make_tracker(threshold=3)
    for _ in range(3):
        tracker.record("cpu", MetricStatus.WARNING)
    tracker.record("cpu", MetricStatus.OK)
    assert tracker.get_entry("cpu") is None


def test_all_recurring_returns_only_threshold_entries():
    tracker = make_tracker(threshold=2)
    tracker.record("a", MetricStatus.WARNING)
    tracker.record("a", MetricStatus.WARNING)
    tracker.record("b", MetricStatus.CRITICAL)  # only once
    recurring = tracker.all_recurring()
    names = [e.metric_name for e in recurring]
    assert "a" in names
    assert "b" not in names


def test_reset_removes_entry():
    tracker = make_tracker()
    tracker.record("cpu", MetricStatus.WARNING)
    tracker.reset("cpu")
    assert tracker.get_entry("cpu") is None


def test_entry_to_dict_has_expected_keys():
    tracker = make_tracker()
    tracker.record("cpu", MetricStatus.WARNING)
    entry = tracker.get_entry("cpu")
    d = entry.to_dict()
    assert "metric_name" in d
    assert "status" in d
    assert "first_seen" in d
    assert "last_seen" in d
    assert "count" in d


def test_result_to_dict_has_expected_keys():
    tracker = make_tracker()
    result = tracker.record("cpu", MetricStatus.WARNING)
    d = result.to_dict()
    assert "metric_name" in d
    assert "status" in d
    assert "count" in d
    assert "is_recurring" in d


def test_multiple_metrics_tracked_independently():
    tracker = make_tracker(threshold=2)
    tracker.record("a", MetricStatus.WARNING)
    tracker.record("b", MetricStatus.CRITICAL)
    tracker.record("a", MetricStatus.WARNING)
    tracker.record("b", MetricStatus.CRITICAL)
    assert tracker.get_entry("a").count == 2
    assert tracker.get_entry("b").count == 2
