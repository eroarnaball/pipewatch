from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from pipewatch.heatmap import HeatmapBuilder, HeatmapCell, MetricHeatmap
from pipewatch.history import MetricHistory, HistoryEntry
from pipewatch.metrics import MetricStatus


def make_history(name: str, entries: list) -> MetricHistory:
    history = MetricHistory(max_entries=200)
    for ts, status in entries:
        entry = HistoryEntry(metric_name=name, value=1.0, status=status, timestamp=ts)
        history.record(entry)
    return history


def test_heatmap_cell_dominant_status_ok():
    cell = HeatmapCell(hour=5)
    assert cell.dominant_status() == "ok"


def test_heatmap_cell_dominant_status_warning():
    cell = HeatmapCell(hour=5, status_counts={"ok": 2, "warning": 1, "critical": 0})
    assert cell.dominant_status() == "warning"


def test_heatmap_cell_dominant_status_critical_takes_priority():
    cell = HeatmapCell(hour=5, status_counts={"ok": 2, "warning": 3, "critical": 1})
    assert cell.dominant_status() == "critical"


def test_heatmap_cell_to_dict_has_expected_keys():
    cell = HeatmapCell(hour=10)
    d = cell.to_dict()
    assert "hour" in d
    assert "status_counts" in d
    assert "dominant_status" in d


def test_build_returns_none_for_unregistered_metric():
    builder = HeatmapBuilder()
    assert builder.build("unknown.metric") is None


def test_build_returns_24_cells():
    base = datetime(2024, 1, 1, 0, 0, 0)
    entries = [(base + timedelta(hours=i), MetricStatus.OK) for i in range(10)]
    history = make_history("test", entries)
    builder = HeatmapBuilder()
    builder.register("test", history)
    result = builder.build("test")
    assert result is not None
    assert len(result.cells) == 24


def test_build_counts_statuses_by_hour():
    base = datetime(2024, 1, 1, 9, 0, 0)  # hour 9
    entries = [
        (base, MetricStatus.WARNING),
        (base + timedelta(minutes=10), MetricStatus.CRITICAL),
        (base + timedelta(hours=1), MetricStatus.OK),  # hour 10
    ]
    history = make_history("m", entries)
    builder = HeatmapBuilder()
    builder.register("m", history)
    result = builder.build("m")
    assert result is not None
    cell_9 = result.cells[9]
    assert cell_9.status_counts["warning"] == 1
    assert cell_9.status_counts["critical"] == 1
    cell_10 = result.cells[10]
    assert cell_10.status_counts["ok"] == 1


def test_build_all_returns_all_registered():
    base = datetime(2024, 1, 1, 6, 0, 0)
    builder = HeatmapBuilder()
    for name in ["a", "b", "c"]:
        history = make_history(name, [(base, MetricStatus.OK)])
        builder.register(name, history)
    results = builder.build_all()
    assert len(results) == 3
    names = {r.metric_name for r in results}
    assert names == {"a", "b", "c"}


def test_metric_heatmap_to_dict_structure():
    base = datetime(2024, 1, 1, 3, 0, 0)
    history = make_history("pipe.lag", [(base, MetricStatus.CRITICAL)])
    builder = HeatmapBuilder()
    builder.register("pipe.lag", history)
    result = builder.build("pipe.lag")
    d = result.to_dict()
    assert d["metric_name"] == "pipe.lag"
    assert isinstance(d["cells"], list)
    assert len(d["cells"]) == 24
