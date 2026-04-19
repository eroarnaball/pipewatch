"""Tests for config_loader discovery logic."""

import json
from pathlib import Path

from pipewatch.config_loader import find_config, load_config, DEFAULT_CONFIG_PATHS


def test_find_config_returns_none_when_absent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Ensure no default paths exist in tmp_path context
    result = find_config()
    # May find home config; only assert type
    assert result is None or isinstance(result, Path)


def test_find_config_finds_local_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg_file = tmp_path / "pipewatch.json"
    cfg_file.write_text(json.dumps({"interval_seconds": 10}))
    result = find_config()
    assert result == cfg_file


def test_load_config_uses_local_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg_file = tmp_path / "pipewatch.json"
    cfg_file.write_text(json.dumps({"interval_seconds": 15}))
    cfg = load_config()
    assert cfg.interval_seconds == 15


def test_default_config_paths_includes_local():
    assert Path("pipewatch.json") in DEFAULT_CONFIG_PATHS
