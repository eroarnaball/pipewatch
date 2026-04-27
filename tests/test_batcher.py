"""Tests for pipewatch.batcher."""

from datetime import datetime, timedelta

import pytest

from pipewatch.alerts import AlertMessage
from pipewatch.batcher import AlertBatcher, AlertBatch, BatchEntry


def make_message(name: str = "metric.a", status: str = "warning") -> AlertMessage:
    return AlertMessage(metric_name=name, status=status, value=1.0, message="test")


def make_batcher(window_seconds: int = 60) -> AlertBatcher:
    return AlertBatcher(window_seconds=window_seconds)


def test_empty_batcher_is_not_ready():
    b = make_batcher()
    assert not b.is_ready()


def test_pending_count_zero_initially():
    b = make_batcher()
    assert b.pending_count() == 0


def test_enqueue_increments_pending_count():
    b = make_batcher()
    b.enqueue(make_message())
    assert b.pending_count() == 1


def test_not_ready_before_window_elapses():
    b = make_batcher(window_seconds=60)
    now = datetime.utcnow()
    b.enqueue(make_message(), now=now)
    assert not b.is_ready(now=now + timedelta(seconds=30))


def test_ready_after_window_elapses():
    b = make_batcher(window_seconds=10)
    now = datetime.utcnow()
    b.enqueue(make_message(), now=now)
    assert b.is_ready(now=now + timedelta(seconds=11))


def test_flush_returns_none_when_empty():
    b = make_batcher()
    assert b.flush() is None


def test_flush_returns_batch_with_correct_size():
    b = make_batcher()
    b.enqueue(make_message("a"))
    b.enqueue(make_message("b"))
    batch = b.flush()
    assert batch is not None
    assert batch.size == 2


def test_flush_clears_queue():
    b = make_batcher()
    b.enqueue(make_message())
    b.flush()
    assert b.pending_count() == 0


def test_flush_resets_window_start():
    b = make_batcher(window_seconds=5)
    now = datetime.utcnow()
    b.enqueue(make_message(), now=now)
    b.flush(now=now + timedelta(seconds=6))
    assert not b.is_ready(now=now + timedelta(seconds=7))


def test_batch_to_dict_has_expected_keys():
    b = make_batcher(window_seconds=30)
    now = datetime.utcnow()
    b.enqueue(make_message("x"), now=now)
    batch = b.flush(now=now)
    assert batch is not None
    d = batch.to_dict()
    assert "size" in d
    assert "window_seconds" in d
    assert "created_at" in d
    assert "entries" in d


def test_batch_entry_to_dict_has_expected_keys():
    msg = make_message("metric.z", "critical")
    entry = BatchEntry(message=msg, queued_at=datetime.utcnow())
    d = entry.to_dict()
    assert "metric_name" in d
    assert "status" in d
    assert "queued_at" in d


def test_multiple_enqueues_preserve_order():
    b = make_batcher()
    names = ["first", "second", "third"]
    for n in names:
        b.enqueue(make_message(n))
    batch = b.flush()
    assert batch is not None
    assert [e.message.metric_name for e in batch.entries] == names
