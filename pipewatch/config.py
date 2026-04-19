"""Configuration loading and validation for pipewatch."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class MetricConfig:
    name: str
    warning: float
    critical: float
    unit: str = ""
    description: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MetricConfig":
        return cls(
            name=data["name"],
            warning=float(data["warning"]),
            critical=float(data["critical"]),
            unit=data.get("unit", ""),
            description=data.get("description", ""),
        )


@dataclass
class PipeWatchConfig:
    metrics: list[MetricConfig] = field(default_factory=list)
    interval_seconds: int = 60
    alert_channels: list[str] = field(default_factory=lambda: ["console"])
    max_history: int = 100

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PipeWatchConfig":
        metrics = [MetricConfig.from_dict(m) for m in data.get("metrics", [])]
        return cls(
            metrics=metrics,
            interval_seconds=int(data.get("interval_seconds", 60)),
            alert_channels=data.get("alert_channels", ["console"]),
            max_history=int(data.get("max_history", 100)),
        )

    @classmethod
    def load(cls, path: str | Path) -> "PipeWatchConfig":
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(path) as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_dict(self) -> dict[str, Any]:
        return {
            "metrics": [
                {
                    "name": m.name,
                    "warning": m.warning,
                    "critical": m.critical,
                    "unit": m.unit,
                    "description": m.description,
                }
                for m in self.metrics
            ],
            "interval_seconds": self.interval_seconds,
            "alert_channels": self.alert_channels,
            "max_history": self.max_history,
        }
