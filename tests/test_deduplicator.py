"""Tests for pipewatch.deduplicator."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from pipewatch.deduplicator import AlertDeduplicator, DeduplicationEntry
from pipewatch.metrics import MetricStatus


def make_deduplicator(window: int = 300) -> AlertDeduplicator:
    return AlertDeduplicator(window_seconds=window)


def test_first_alert_is_not_duplicate():
    d = make_deduplicator()
    assert d.is_duplicate("row_count", MetricStatus.WARNING) is False


def test_record_creates_entry():
    d = make_deduplicator()
    entry = d.record("row_count", MetricStatus.WARNING)
    assert isinstance(entry, DeduplicationEntry)
    assert entry.metric_name == "row_count"
    assert entry.status == MetricStatus.WARNING
    assert entry.count == 1


def test_second_alert_within_window_is_duplicate():
    d = make_deduplicator(window=60)
    d.record("row_count", MetricStatus.CRITICAL)
    assert d.is_duplicate("row_count", MetricStatus.CRITICAL) is True


def test_second_alert_after_window_is_not_duplicate():
    d = make_deduplicator(window=60)
    past = datetime.utcnow() - timedelta(seconds=120)
    d.record("row_count", MetricStatus.CRITICAL)
    # Manually backdate the last_seen timestamp
    key = ("row_count", MetricStatus.CRITICAL.value)
    d._entries[key].last_seen = past
    assert d.is_duplicate("row_count", MetricStatus.CRITICAL) is False


def test_record_increments_count():
    d = make_deduplicator()
    d.record("lag", MetricStatus.WARNING)
    d.record("lag", MetricStatus.WARNING)
    key = ("lag", MetricStatus.WARNING.value)
    assert d._entries[key].count == 2


def test_different_statuses_tracked_independently():
    d = make_deduplicator()
    d.record("lag", MetricStatus.WARNING)
    assert d.is_duplicate("lag", MetricStatus.CRITICAL) is False


def test_clear_removes_specific_status():
    d = make_deduplicator()
    d.record("lag", MetricStatus.WARNING)
    d.record("lag", MetricStatus.CRITICAL)
    d.clear("lag", MetricStatus.WARNING)
    assert d.is_duplicate("lag", MetricStatus.WARNING) is False
    assert d.is_duplicate("lag", MetricStatus.CRITICAL) is True


def test_clear_all_statuses_for_metric():
    d = make_deduplicator()
    d.record("lag", MetricStatus.WARNING)
    d.record("lag", MetricStatus.CRITICAL)
    d.clear("lag")
    assert d.is_duplicate("lag", MetricStatus.WARNING) is False
    assert d.is_duplicate("lag", MetricStatus.CRITICAL) is False


def test_all_entries_returns_list_of_dicts():
    d = make_deduplicator()
    d.record("a", MetricStatus.WARNING)
    d.record("b", MetricStatus.CRITICAL)
    entries = d.all_entries()
    assert len(entries) == 2
    assert all("metric_name" in e for e in entries)
    assert all("count" in e for e in entries)


def test_entry_to_dict_has_expected_keys():
    d = make_deduplicator()
    entry = d.record("pipeline_x", MetricStatus.CRITICAL)
    result = entry.to_dict()
    assert set(result.keys()) == {"metric_name", "status", "first_seen", "last_seen", "count"}
