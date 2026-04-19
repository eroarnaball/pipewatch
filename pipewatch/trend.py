"""Trend detection for pipeline metrics based on recent history."""

from enum import Enum
from typing import List, Optional
from pipewatch.history import MetricHistory, HistoryEntry
from pipewatch.metrics import MetricStatus


class TrendDirection(str, Enum):
    IMPROVING = "improving"
    DEGRADING = "degrading"
    STABLE = "stable"
    INSUFFICIENT_DATA = "insufficient_data"


def detect_trend(
    history: MetricHistory,
    metric_name: str,
    window: int = 5,
) -> TrendDirection:
    """Detect trend direction from the last `window` entries for a metric."""
    entries: List[HistoryEntry] = [
        e for e in history.entries if e.metric_name == metric_name
    ][-window:]

    if len(entries) < 2:
        return TrendDirection.INSUFFICIENT_DATA

    values = [e.value for e in entries if e.value is not None]
    if len(values) < 2:
        return TrendDirection.INSUFFICIENT_DATA

    deltas = [values[i + 1] - values[i] for i in range(len(values) - 1)]
    avg_delta = sum(deltas) / len(deltas)

    threshold = 0.05 * (max(values) - min(values) or 1)
    if avg_delta > threshold:
        return TrendDirection.DEGRADING
    elif avg_delta < -threshold:
        return TrendDirection.IMPROVING
    return TrendDirection.STABLE


def status_trend(
    history: MetricHistory,
    metric_name: str,
    window: int = 5,
) -> TrendDirection:
    """Detect trend from status severity (OK=0, WARNING=1, CRITICAL=2)."""
    _severity = {MetricStatus.OK: 0, MetricStatus.WARNING: 1, MetricStatus.CRITICAL: 2}
    entries = [
        e for e in history.entries if e.metric_name == metric_name
    ][-window:]

    if len(entries) < 2:
        return TrendDirection.INSUFFICIENT_DATA

    scores = [_severity.get(e.status, 0) for e in entries]
    if scores[-1] > scores[0]:
        return TrendDirection.DEGRADING
    elif scores[-1] < scores[0]:
        return TrendDirection.IMPROVING
    return TrendDirection.STABLE
