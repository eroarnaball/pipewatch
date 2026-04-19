"""Tests for pipewatch.replay."""

import pytest
from pipewatch.history import MetricHistory
from pipewatch.metrics import PipelineMetric, MetricEvaluation, MetricStatus
from pipewatch.replay import MetricReplayer, ReplayFrame


def make_history(values_statuses):
    h = MetricHistory(max_entries=50)
    for v, s in values_statuses:
        m = PipelineMetric(name="test", value=v, unit="ms")
        ev = MetricEvaluation(metric=m, status=s, message="")
        h.record(ev)
    return h


def test_frames_count_matches_history():
    h = make_history([(1, MetricStatus.OK), (2, MetricStatus.WARNING)])
    r = MetricReplayer(h)
    assert len(r.frames()) == 2


def test_frame_indices_are_sequential():
    h = make_history([(i, MetricStatus.OK) for i in range(5)])
    r = MetricReplayer(h)
    indices = [f.index for f in r.frames()]
    assert indices == list(range(5))


def test_slice_returns_correct_range():
    h = make_history([(i, MetricStatus.OK) for i in range(10)])
    r = MetricReplayer(h)
    sliced = r.slice(2, 5)
    assert len(sliced) == 3
    assert sliced[0].index == 2
    assert sliced[-1].index == 4


def test_filter_by_status():
    data = [
        (10, MetricStatus.OK),
        (50, MetricStatus.WARNING),
        (90, MetricStatus.CRITICAL),
        (20, MetricStatus.OK),
    ]
    h = make_history(data)
    r = MetricReplayer(h)
    ok_frames = r.filter_by_status(MetricStatus.OK)
    assert len(ok_frames) == 2
    for f in ok_frames:
        assert f.entry.status == MetricStatus.OK


def test_first_occurrence_found():
    data = [(10, MetricStatus.OK), (50, MetricStatus.WARNING), (90, MetricStatus.CRITICAL)]
    h = make_history(data)
    r = MetricReplayer(h)
    frame = r.first_occurrence(MetricStatus.WARNING)
    assert frame is not None
    assert frame.index == 1


def test_first_occurrence_not_found():
    h = make_history([(10, MetricStatus.OK), (20, MetricStatus.OK)])
    r = MetricReplayer(h)
    assert r.first_occurrence(MetricStatus.CRITICAL) is None


def test_summary_counts():
    data = [
        (1, MetricStatus.OK),
        (2, MetricStatus.WARNING),
        (3, MetricStatus.CRITICAL),
        (4, MetricStatus.OK),
    ]
    h = make_history(data)
    r = MetricReplayer(h)
    s = r.summary()
    assert s["total"] == 4
    assert s["ok"] == 2
    assert s["warning"] == 1
    assert s["critical"] == 1


def test_frame_to_dict_has_index():
    h = make_history([(42, MetricStatus.OK)])
    r = MetricReplayer(h)
    d = r.frames()[0].to_dict()
    assert "index" in d
    assert "entry" in d
