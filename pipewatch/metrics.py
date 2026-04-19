"""Core metrics data structures for pipeline health monitoring."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class MetricStatus(Enum):
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class PipelineMetric:
    """Represents a single pipeline health metric snapshot."""
    pipeline_name: str
    metric_name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    unit: Optional[str] = None
    tags: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "pipeline_name": self.pipeline_name,
            "metric_name": self.metric_name,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "unit": self.unit,
            "tags": self.tags,
        }


@dataclass
class MetricEvaluation:
    """Result of evaluating a metric against thresholds."""
    metric: PipelineMetric
    status: MetricStatus
    message: str
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
