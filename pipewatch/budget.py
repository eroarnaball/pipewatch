"""Metric budget tracking: define allowed error budgets and track burn rate."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pipewatch.metrics import MetricStatus
from pipewatch.history import MetricHistory


@dataclass
class BudgetConfig:
    """Defines an error budget for a metric."""
    metric_name: str
    window_size: int  # number of recent entries to consider
    allowed_critical_ratio: float  # e.g. 0.05 = 5% critical allowed
    allowed_warning_ratio: float   # e.g. 0.20 = 20% warning allowed

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "window_size": self.window_size,
            "allowed_critical_ratio": self.allowed_critical_ratio,
            "allowed_warning_ratio": self.allowed_warning_ratio,
        }


@dataclass
class BudgetResult:
    """Result of evaluating a metric against its error budget."""
    metric_name: str
    window_size: int
    critical_ratio: float
    warning_ratio: float
    allowed_critical_ratio: float
    allowed_warning_ratio: float
    critical_budget_exceeded: bool
    warning_budget_exceeded: bool

    @property
    def any_exceeded(self) -> bool:
        return self.critical_budget_exceeded or self.warning_budget_exceeded

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "window_size": self.window_size,
            "critical_ratio": round(self.critical_ratio, 4),
            "warning_ratio": round(self.warning_ratio, 4),
            "allowed_critical_ratio": self.allowed_critical_ratio,
            "allowed_warning_ratio": self.allowed_warning_ratio,
            "critical_budget_exceeded": self.critical_budget_exceeded,
            "warning_budget_exceeded": self.warning_budget_exceeded,
        }


class ErrorBudgetTracker:
    """Tracks error budgets across metrics."""

    def __init__(self) -> None:
        self._budgets: Dict[str, BudgetConfig] = {}

    def register(self, config: BudgetConfig) -> None:
        self._budgets[config.metric_name] = config

    def get(self, metric_name: str) -> Optional[BudgetConfig]:
        return self._budgets.get(metric_name)

    def evaluate(self, metric_name: str, history: MetricHistory) -> Optional[BudgetResult]:
        config = self._budgets.get(metric_name)
        if config is None:
            return None
        entries = history.entries[-config.window_size:]
        if not entries:
            return BudgetResult(
                metric_name=metric_name,
                window_size=0,
                critical_ratio=0.0,
                warning_ratio=0.0,
                allowed_critical_ratio=config.allowed_critical_ratio,
                allowed_warning_ratio=config.allowed_warning_ratio,
                critical_budget_exceeded=False,
                warning_budget_exceeded=False,
            )
        total = len(entries)
        critical_count = sum(1 for e in entries if e.status == MetricStatus.CRITICAL)
        warning_count = sum(1 for e in entries if e.status == MetricStatus.WARNING)
        critical_ratio = critical_count / total
        warning_ratio = warning_count / total
        return BudgetResult(
            metric_name=metric_name,
            window_size=total,
            critical_ratio=critical_ratio,
            warning_ratio=warning_ratio,
            allowed_critical_ratio=config.allowed_critical_ratio,
            allowed_warning_ratio=config.allowed_warning_ratio,
            critical_budget_exceeded=critical_ratio > config.allowed_critical_ratio,
            warning_budget_exceeded=warning_ratio > config.allowed_warning_ratio,
        )
