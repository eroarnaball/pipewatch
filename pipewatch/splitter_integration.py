"""Integration helpers: wire AlertSplitter into a pipeline run."""
from dataclasses import dataclass, field
from typing import List
from pipewatch.splitter import AlertSplitter, SplitResult
from pipewatch.alerts import AlertMessage
from pipewatch.metrics import MetricStatus


@dataclass
class SplitterRunSummary:
    total: int = 0
    dispatched: int = 0
    fully_skipped: int = 0
    results: List[SplitResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "dispatched": self.dispatched,
            "fully_skipped": self.fully_skipped,
        }


class SplitterRunner:
    """Runs a list of AlertMessages through an AlertSplitter and collects results."""

    def __init__(self, splitter: AlertSplitter) -> None:
        self._splitter = splitter

    def run(self, messages: List[AlertMessage], skip_ok: bool = True) -> SplitterRunSummary:
        summary = SplitterRunSummary()
        for msg in messages:
            if skip_ok and msg.status.lower() == MetricStatus.OK.value.lower():
                continue
            summary.total += 1
            result = self._splitter.dispatch(msg)
            summary.results.append(result)
            if result.dispatched_to:
                summary.dispatched += 1
            else:
                summary.fully_skipped += 1
        return summary
