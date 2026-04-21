"""Alert debouncer: suppress alerts until a condition persists for N consecutive checks."""

from dataclasses import dataclass, field
from typing import Dict, Optional
from pipewatch.metrics import MetricStatus


@dataclass
class DebounceState:
    metric_name: str
    current_status: MetricStatus
    consecutive_count: int = 0

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "current_status": self.current_status.value,
            "consecutive_count": self.consecutive_count,
        }


@dataclass
class DebounceResult:
    metric_name: str
    status: MetricStatus
    suppressed: bool
    consecutive_count: int
    threshold: int

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "status": self.status.value,
            "suppressed": self.suppressed,
            "consecutive_count": self.consecutive_count,
            "threshold": self.threshold,
        }


class AlertDebouncer:
    """Suppress non-OK alerts until they persist for `threshold` consecutive evaluations."""

    def __init__(self, threshold: int = 3) -> None:
        if threshold < 1:
            raise ValueError("threshold must be >= 1")
        self.threshold = threshold
        self._states: Dict[str, DebounceState] = {}

    def evaluate(self, metric_name: str, status: MetricStatus) -> DebounceResult:
        state = self._states.get(metric_name)

        if status == MetricStatus.OK:
            # Reset on recovery
            self._states.pop(metric_name, None)
            return DebounceResult(
                metric_name=metric_name,
                status=status,
                suppressed=False,
                consecutive_count=0,
                threshold=self.threshold,
            )

        if state is None or state.current_status != status:
            state = DebounceState(metric_name=metric_name, current_status=status, consecutive_count=1)
        else:
            state.consecutive_count += 1

        self._states[metric_name] = state
        suppressed = state.consecutive_count < self.threshold

        return DebounceResult(
            metric_name=metric_name,
            status=status,
            suppressed=suppressed,
            consecutive_count=state.consecutive_count,
            threshold=self.threshold,
        )

    def reset(self, metric_name: str) -> None:
        self._states.pop(metric_name, None)

    def state_for(self, metric_name: str) -> Optional[DebounceState]:
        return self._states.get(metric_name)
