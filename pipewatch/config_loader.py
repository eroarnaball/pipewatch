"""Utilities for resolving and writing pipewatch config files."""

from __future__ import annotations

import json
from pathlib import Path

from pipewatch.config import PipeWatchConfig

DEFAULT_CONFIG_PATHS = [
    Path("pipewatch.json"),
    Path(".pipewatch") / "config.json",
    Path.home() / ".config" / "pipewatch" / "config.json",
]


def find_config() -> Path | None:
    """Search default locations for a config file."""
    for path in DEFAULT_CONFIG_PATHS:
        if path.exists():
            return path
    return None


def load_config(path: str | Path | None = None) -> PipeWatchConfig:
    """Load config from an explicit path or auto-discover it."""
    if path is not None:
        return PipeWatchConfig.load(path)
    discovered = find_config()
    if discovered is None:
        return PipeWatchConfig()
    return PipeWatchConfig.load(discovered)


def write_default_config(path: str | Path = "pipewatch.json") -> Path:
    """Write a default config file to the given path."""
    path = Path(path)
    default = PipeWatchConfig(
        metrics=[
            {
                "name": "example_metric",
                "warning": 80.0,
                "critical": 95.0,
                "unit": "%",
                "description": "An example metric",
            }
        ],
        interval_seconds=60,
        alert_channels=["console"],
        max_history=100,
    )
    # Build raw dict manually so we don't depend on MetricConfig objects here
    raw = {
        "metrics": [
            {"name": "example_metric", "warning": 80.0, "critical": 95.0,
             "unit": "%", "description": "An example metric"}
        ],
        "interval_seconds": 60,
        "alert_channels": ["console"],
        "max_history": 100,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(raw, f, indent=2)
    return path
