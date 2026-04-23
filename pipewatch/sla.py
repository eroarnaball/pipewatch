from dataclasses import dataclass, field
from typing import Dict, Optional
from pipewatch.metrics import MetricStatus
from pipewatch.history import MetricHistory


@dataclass
class SLAConfig:
    metric_name: str
    max_critical_ratio: float = 0.01  # e.g. 1% critical allowed
    max_warning_ratio: float = 0.05   # e.g. 5% warning allowed

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "max_critical_ratio": self.max_critical_ratio,
            "max_warning_ratio": self.max_warning_ratio,
        }


@dataclass
class SLAResult:
    metric_name: str
    critical_ratio: float
    warning_ratio: float
    critical_breached: bool
    warning_breached: bool
    total_entries: int

    @property
    def any_breached(self) -> bool:
        return self.critical_breached or self.warning_breached

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "critical_ratio": round(self.critical_ratio, 4),
            "warning_ratio": round(self.warning_ratio, 4),
            "critical_breached": self.critical_breached,
            "warning_breached": self.warning_breached,
            "total_entries": self.total_entries,
            "any_breached": self.any_breached,
        }


class SLATracker:
    def __init__(self) -> None:
        self._configs: Dict[str, SLAConfig] = {}

    def register(self, config: SLAConfig) -> None:
        self._configs[config.metric_name] = config

    def evaluate(self, metric_name: str, history: MetricHistory) -> Optional[SLAResult]:
        config = self._configs.get(metric_name)
        if config is None:
            return None

        entries = history.entries(metric_name)
        total = len(entries)
        if total == 0:
            return SLAResult(
                metric_name=metric_name,
                critical_ratio=0.0,
                warning_ratio=0.0,
                critical_breached=False,
                warning_breached=False,
                total_entries=0,
            )

        critical_count = sum(1 for e in entries if e.status == MetricStatus.CRITICAL)
        warning_count = sum(1 for e in entries if e.status == MetricStatus.WARNING)
        critical_ratio = critical_count / total
        warning_ratio = warning_count / total

        return SLAResult(
            metric_name=metric_name,
            critical_ratio=critical_ratio,
            warning_ratio=warning_ratio,
            critical_breached=critical_ratio > config.max_critical_ratio,
            warning_breached=warning_ratio > config.max_warning_ratio,
            total_entries=total,
        )

    def evaluate_all(self, history: MetricHistory) -> Dict[str, SLAResult]:
        results = {}
        for name in self._configs:
            result = self.evaluate(name, history)
            if result is not None:
                results[name] = result
        return results
