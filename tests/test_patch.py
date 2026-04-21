"""Tests for pipewatch.patch — MetricPatcher for overriding metric values."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch as mock_patch

from pipewatch.patch import PatchEntry, MetricPatcher
from pipewatch.metrics import MetricStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_patcher() -> MetricPatcher:
    return MetricPatcher()


def _now() -> datetime:
    return datetime.utcnow()


# ---------------------------------------------------------------------------
# PatchEntry.is_active
# ---------------------------------------------------------------------------

def test_patch_entry_active_within_window():
    start = _now() - timedelta(minutes=1)
    end = _now() + timedelta(minutes=5)
    entry = PatchEntry(
        metric_name="latency",
        override_status=MetricStatus.OK,
        reason="maintenance",
        start=start,
        end=end,
    )
    assert entry.is_active() is True


def test_patch_entry_inactive_before_start():
    start = _now() + timedelta(minutes=10)
    end = _now() + timedelta(minutes=20)
    entry = PatchEntry(
        metric_name="latency",
        override_status=MetricStatus.OK,
        reason="scheduled",
        start=start,
        end=end,
    )
    assert entry.is_active() is False


def test_patch_entry_inactive_after_end():
    start = _now() - timedelta(minutes=20)
    end = _now() - timedelta(minutes=5)
    entry = PatchEntry(
        metric_name="latency",
        override_status=MetricStatus.OK,
        reason="expired",
        start=start,
        end=end,
    )
    assert entry.is_active() is False


def test_patch_entry_indefinite_no_end():
    """A patch with no end time should remain active indefinitely."""
    start = _now() - timedelta(hours=1)
    entry = PatchEntry(
        metric_name="latency",
        override_status=MetricStatus.WARNING,
        reason="indefinite override",
        start=start,
        end=None,
    )
    assert entry.is_active() is True


# ---------------------------------------------------------------------------
# PatchEntry.to_dict
# ---------------------------------------------------------------------------

def test_patch_entry_to_dict_contains_expected_keys():
    start = _now()
    entry = PatchEntry(
        metric_name="throughput",
        override_status=MetricStatus.CRITICAL,
        reason="test",
        start=start,
        end=None,
    )
    d = entry.to_dict()
    assert "metric_name" in d
    assert "override_status" in d
    assert "reason" in d
    assert "start" in d
    assert "end" in d
    assert d["metric_name"] == "throughput"
    assert d["override_status"] == MetricStatus.CRITICAL.value


# ---------------------------------------------------------------------------
# MetricPatcher.apply / is_patched
# ---------------------------------------------------------------------------

def test_apply_creates_active_patch():
    patcher = make_patcher()
    patcher.apply(
        metric_name="error_rate",
        override_status=MetricStatus.OK,
        reason="known issue",
    )
    assert patcher.is_patched("error_rate") is True


def test_is_patched_returns_false_for_unknown():
    patcher = make_patcher()
    assert patcher.is_patched("nonexistent") is False


def test_remove_clears_patch():
    patcher = make_patcher()
    patcher.apply(
        metric_name="queue_depth",
        override_status=MetricStatus.WARNING,
        reason="temp",
    )
    patcher.remove("queue_depth")
    assert patcher.is_patched("queue_depth") is False


def test_get_override_returns_status_when_patched():
    patcher = make_patcher()
    patcher.apply(
        metric_name="lag",
        override_status=MetricStatus.OK,
        reason="planned downtime",
    )
    result = patcher.get_override("lag")
    assert result == MetricStatus.OK


def test_get_override_returns_none_when_not_patched():
    patcher = make_patcher()
    result = patcher.get_override("lag")
    assert result is None


def test_list_active_patches_returns_only_active():
    patcher = make_patcher()
    past_start = _now() - timedelta(hours=2)
    past_end = _now() - timedelta(hours=1)

    # Active patch
    patcher.apply("active_metric", MetricStatus.OK, "active")

    # Expired patch — inject directly
    expired = PatchEntry(
        metric_name="expired_metric",
        override_status=MetricStatus.WARNING,
        reason="old",
        start=past_start,
        end=past_end,
    )
    patcher._patches["expired_metric"] = expired

    active = patcher.list_active()
    names = [e.metric_name for e in active]
    assert "active_metric" in names
    assert "expired_metric" not in names
