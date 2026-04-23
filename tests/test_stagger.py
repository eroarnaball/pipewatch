"""Tests for pipewatch.stagger."""

from __future__ import annotations

import time

import pytest

from pipewatch.stagger import AlertStagger, StaggeredAlert
from pipewatch.alerts import AlertMessage
from pipewatch.metrics import MetricStatus


def make_message(name: str = "test.metric", status: MetricStatus = MetricStatus.WARNING) -> AlertMessage:
    return AlertMessage(
        metric_name=name,
        status=status,
        value=1.0,
        message=f"{name} alert",
    )


def make_stagger(interval: float = 5.0) -> AlertStagger:
    return AlertStagger(interval_seconds=interval)


def test_enqueue_returns_staggered_alert():
    s = make_stagger()
    msg = make_message()
    entry = s.enqueue(msg)
    assert isinstance(entry, StaggeredAlert)
    assert entry.message is msg
    assert not entry.sent


def test_first_enqueue_scheduled_immediately():
    s = make_stagger(interval=10.0)
    before = time.time()
    entry = s.enqueue(make_message())
    after = time.time()
    assert before <= entry.scheduled_at <= after + 0.1


def test_second_enqueue_offset_by_interval():
    s = make_stagger(interval=10.0)
    first = s.enqueue(make_message("m1"))
    second = s.enqueue(make_message("m2"))
    assert second.scheduled_at >= first.scheduled_at + 10.0


def test_due_returns_only_past_alerts():
    s = make_stagger(interval=60.0)
    s.enqueue(make_message("m1"))
    s.enqueue(make_message("m2"))  # scheduled 60s later
    now = time.time()
    due = s.due(now=now + 1)
    assert len(due) == 1
    assert due[0].message.metric_name == "m1"


def test_flush_marks_alerts_sent():
    s = make_stagger(interval=1.0)
    s.enqueue(make_message("m1"))
    s.enqueue(make_message("m2"))
    flushed = s.flush(now=time.time() + 200)
    assert all(a.sent for a in flushed)
    assert len(flushed) == 2


def test_pending_excludes_sent():
    s = make_stagger(interval=1.0)
    s.enqueue(make_message("m1"))
    s.enqueue(make_message("m2"))
    s.flush(now=time.time() + 200)
    assert s.queue_size() == 0
    assert s.pending() == []


def test_to_dict_has_expected_keys():
    s = make_stagger()
    entry = s.enqueue(make_message())
    d = entry.to_dict()
    assert "metric" in d
    assert "status" in d
    assert "scheduled_at" in d
    assert "sent" in d


def test_multiple_enqueues_increase_queue_size():
    s = make_stagger(interval=5.0)
    for i in range(4):
        s.enqueue(make_message(f"m{i}"))
    assert s.queue_size() == 4
