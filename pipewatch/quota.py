from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional
from pipewatch.metrics import MetricStatus
from pipewatch.history import MetricHistory


@dataclass
class QuotaConfig:
    max_warnings_pct: float = 0.25  # fraction of entries allowed to be WARNING
    max_critical_pct: float = 0.10  # fraction of entries allowed to be CRITICAL

    def to_dict(self) -> dict:
        return {
            "max_warnings_pct": self.max_warnings_pct,
            "max_critical_pct": self.max_critical_pct,
        }


@dataclass
class QuotaResult:
    metric_name: str
    total: int
    warning_count: int
    critical_count: int
    warning_pct: float
    critical_pct: float
    warning_exceeded: bool
    critical_exceeded: bool

    @property
    def any_exceeded(self) -> bool:
        return self.warning_exceeded or self.critical_exceeded

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "total": self.total,
            "warning_count": self.warning_count,
            "critical_count": self.critical_count,
            "warning_pct": round(self.warning_pct, 4),
            "critical_pct": round(self.critical_pct, 4),
            "warning_exceeded": self.warning_exceeded,
            "critical_exceeded": self.critical_exceeded,
        }


class QuotaTracker:
    def __init__(self, default_config: Optional[QuotaConfig] = None) -> None:
        self._default = default_config or QuotaConfig()
        self._overrides: Dict[str, QuotaConfig] = {}

    def register(self, metric_name: str, config: QuotaConfig) -> None:
        self._overrides[metric_name] = config

    def _config_for(self, metric_name: str) -> QuotaConfig:
        return self._overrides.get(metric_name, self._default)

    def evaluate(self, metric_name: str, history: MetricHistory) -> Optional[QuotaResult]:
        entries = history.entries_for(metric_name)
        if not entries:
            return None
        cfg = self._config_for(metric_name)
        total = len(entries)
        warning_count = sum(1 for e in entries if e.status == MetricStatus.WARNING)
        critical_count = sum(1 for e in entries if e.status == MetricStatus.CRITICAL)
        warning_pct = warning_count / total
        critical_pct = critical_count / total
        return QuotaResult(
            metric_name=metric_name,
            total=total,
            warning_count=warning_count,
            critical_count=critical_count,
            warning_pct=warning_pct,
            critical_pct=critical_pct,
            warning_exceeded=warning_pct > cfg.max_warnings_pct,
            critical_exceeded=critical_pct > cfg.max_critical_pct,
        )
