"""Tests for pipewatch config loading and validation."""

import json
import pytest
from pathlib import Path

from pipewatch.config import MetricConfig, PipeWatchConfig
from pipewatch.config_loader import load_config, write_default_config


SAMPLE = {
    "metrics": [
        {"name": "lag", "warning": 100.0, "critical": 500.0, "unit": "ms", "description": "Queue lag"}
    ],
    "interval_seconds": 30,
    "alert_channels": ["console"],
    "max_history": 50,
}


def test_metric_config_from_dict():
    mc = MetricConfig.from_dict(SAMPLE["metrics"][0])
    assert mc.name == "lag"
    assert mc.warning == 100.0
    assert mc.critical == 500.0
    assert mc.unit == "ms"


def test_pipewatch_config_from_dict():
    cfg = PipeWatchConfig.from_dict(SAMPLE)
    assert len(cfg.metrics) == 1
    assert cfg.interval_seconds == 30
    assert cfg.max_history == 50


def test_config_defaults_when_empty():
    cfg = PipeWatchConfig.from_dict({})
    assert cfg.metrics == []
    assert cfg.interval_seconds == 60
    assert cfg.alert_channels == ["console"]


def test_config_load_from_file(tmp_path):
    cfg_file = tmp_path / "pipewatch.json"
    cfg_file.write_text(json.dumps(SAMPLE))
    cfg = PipeWatchConfig.load(cfg_file)
    assert cfg.metrics[0].name == "lag"


def test_config_load_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        PipeWatchConfig.load(tmp_path / "nonexistent.json")


def test_config_to_dict_roundtrip():
    cfg = PipeWatchConfig.from_dict(SAMPLE)
    d = cfg.to_dict()
    assert d["interval_seconds"] == 30
    assert d["metrics"][0]["name"] == "lag"


def test_write_default_config_creates_file(tmp_path):
    out = tmp_path / "pipewatch.json"
    write_default_config(out)
    assert out.exists()
    data = json.loads(out.read_text())
    assert "metrics" in data


def test_load_config_returns_default_when_no_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = load_config()
    assert isinstance(cfg, PipeWatchConfig)


def test_load_config_explicit_path(tmp_path):
    cfg_file = tmp_path / "custom.json"
    cfg_file.write_text(json.dumps(SAMPLE))
    cfg = load_config(cfg_file)
    assert cfg.interval_seconds == 30
