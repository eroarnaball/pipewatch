"""Metric collection registry for pipeline monitors."""
from datetime import datetime
from typing import Callable, Dict, List

from pipewatch.metrics import PipelineMetric


CollectorFn = Callable[[], float]


class MetricCollector:
    """Registry that holds named collector functions per pipeline."""

    def __init__(self):
        self._collectors: Dict[str, Dict[str, CollectorFn]] = {}

    def register(self, pipeline_name: str, metric_name: str, fn: CollectorFn, unit: str = None, tags: dict = None):
        """Register a callable that returns the current metric value."""
        self._collectors.setdefault(pipeline_name, {})[metric_name] = {
            "fn": fn,
            "unit": unit,
            "tags": tags or {},
        }

    def collect_all(self) -> List[PipelineMetric]:
        """Run all registered collectors and return metric snapshots."""
        results = []
        now = datetime.utcnow()
        for pipeline_name, metrics in self._collectors.items():
            for metric_name, cfg in metrics.items():
                try:
                    value = cfg["fn"]()
                    results.append(
                        PipelineMetric(
                            pipeline_name=pipeline_name,
                            metric_name=metric_name,
                            value=float(value),
                            timestamp=now,
                            unit=cfg["unit"],
                            tags=cfg["tags"],
                        )
                    )
                except Exception as exc:  # noqa: BLE001
                    print(f"[collector] error collecting {pipeline_name}/{metric_name}: {exc}")
        return results
