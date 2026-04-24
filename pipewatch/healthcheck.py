from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from pipewatch.metrics import MetricStatus


@dataclass
class HealthCheckResult:
    name: str
    status: MetricStatus
    message: str
    checked_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "checked_at": self.checked_at.isoformat(),
        }


@dataclass
class HealthSummary:
    results: List[HealthCheckResult]

    @property
    def overall(self) -> MetricStatus:
        statuses = {r.status for r in self.results}
        if MetricStatus.CRITICAL in statuses:
            return MetricStatus.CRITICAL
        if MetricStatus.WARNING in statuses:
            return MetricStatus.WARNING
        return MetricStatus.OK

    @property
    def failed(self) -> List[HealthCheckResult]:
        return [r for r in self.results if r.status != MetricStatus.OK]

    def to_dict(self) -> dict:
        return {
            "overall": self.overall.value,
            "total": len(self.results),
            "failed_count": len(self.failed),
            "results": [r.to_dict() for r in self.results],
        }


class HealthChecker:
    def __init__(self) -> None:
        self._checks: Dict[str, object] = {}

    def register(self, name: str, fn) -> None:
        self._checks[name] = fn

    def run(self, name: str) -> Optional[HealthCheckResult]:
        fn = self._checks.get(name)
        if fn is None:
            return None
        try:
            status, message = fn()
            return HealthCheckResult(name=name, status=status, message=message)
        except Exception as exc:  # noqa: BLE001
            return HealthCheckResult(
                name=name,
                status=MetricStatus.CRITICAL,
                message=f"Check raised exception: {exc}",
            )

    def run_all(self) -> HealthSummary:
        results = [self.run(name) for name in self._checks]
        return HealthSummary(results=[r for r in results if r is not None])
