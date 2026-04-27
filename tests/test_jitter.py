"""Tests for pipewatch.jitter."""

from __future__ import annotations

from datetime import datetime

import pytest
from click.testing import CliRunner

from pipewatch.alerts import AlertMessage
from pipewatch.jitter import AlertJitter, JitteredAlert
from pipewatch.jitter_cli import jitter
from pipewatch.metrics import MetricStatus


def make_message(name: str = "test.metric", status: str = MetricStatus.WARNING) -> AlertMessage:
    return AlertMessage(metric_name=name, status=status, value=10.0, threshold=5.0)


def make_jitter(max_jitter: float = 30.0, seed: int = 0) -> AlertJitter:
    j = AlertJitter(max_jitter_seconds=max_jitter)
    j.seed(seed)
    return j


def test_schedule_returns_jittered_alert():
    j = make_jitter()
    msg = make_message()
    base = datetime(2024, 6, 1, 0, 0, 0)
    result = j.schedule(msg, base_time=base)
    assert isinstance(result, JitteredAlert)
    assert result.message is msg


def test_jitter_seconds_within_bounds():
    j = make_jitter(max_jitter=60.0)
    base = datetime(2024, 6, 1, 0, 0, 0)
    for _ in range(50):
        result = j.schedule(make_message(), base_time=base)
        assert 0.0 <= result.jitter_seconds <= 60.0


def test_scheduled_at_is_after_base_time():
    j = make_jitter()
    base = datetime(2024, 6, 1, 12, 0, 0)
    result = j.schedule(make_message(), base_time=base)
    assert result.scheduled_at >= base


def test_schedule_batch_returns_correct_count():
    j = make_jitter()
    base = datetime(2024, 6, 1, 0, 0, 0)
    messages = [make_message(name=f"m{i}") for i in range(5)]
    results = j.schedule_batch(messages, base_time=base)
    assert len(results) == 5


def test_schedule_batch_independent_jitter():
    j = make_jitter(max_jitter=30.0, seed=99)
    base = datetime(2024, 6, 1, 0, 0, 0)
    messages = [make_message(name=f"m{i}") for i in range(3)]
    results = j.schedule_batch(messages, base_time=base)
    jitters = [r.jitter_seconds for r in results]
    assert len(set(jitters)) > 1  # highly unlikely to all be equal


def test_to_dict_has_expected_keys():
    j = make_jitter()
    base = datetime(2024, 6, 1, 0, 0, 0)
    result = j.schedule(make_message(), base_time=base)
    d = result.to_dict()
    assert "metric" in d
    assert "status" in d
    assert "scheduled_at" in d
    assert "jitter_seconds" in d


def test_zero_max_jitter_gives_zero_delay():
    j = make_jitter(max_jitter=0.0)
    base = datetime(2024, 6, 1, 0, 0, 0)
    result = j.schedule(make_message(), base_time=base)
    assert result.jitter_seconds == 0.0
    assert result.scheduled_at == base


# CLI tests

@pytest.fixture
def runner():
    return CliRunner()


def test_schedule_table_output_contains_headers(runner):
    result = runner.invoke(jitter, ["schedule"])
    assert result.exit_code == 0
    assert "Metric" in result.output
    assert "Jitter" in result.output


def test_schedule_json_output_is_valid(runner):
    import json
    result = runner.invoke(jitter, ["schedule", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) > 0


def test_schedule_json_contains_expected_keys(runner):
    import json
    result = runner.invoke(jitter, ["schedule", "--format", "json"])
    data = json.loads(result.output)
    for entry in data:
        assert "metric" in entry
        assert "jitter_seconds" in entry
        assert "scheduled_at" in entry
