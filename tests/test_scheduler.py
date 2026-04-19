"""Tests for PipelineScheduler."""

import time
import pytest
from pipewatch.scheduler import PipelineScheduler, ScheduledJob


def test_job_is_due_on_first_run():
    job = ScheduledJob(name="test", fn=lambda: None, interval_seconds=10)
    assert job.is_due(time.monotonic()) is True


def test_job_not_due_before_interval():
    job = ScheduledJob(name="test", fn=lambda: None, interval_seconds=60)
    job.last_run = time.monotonic()
    assert job.is_due(time.monotonic()) is False


def test_job_due_after_interval():
    job = ScheduledJob(name="test", fn=lambda: None, interval_seconds=1)
    job.last_run = time.monotonic() - 2
    assert job.is_due(time.monotonic()) is True


def test_register_adds_job():
    scheduler = PipelineScheduler()
    scheduler.register("my_job", lambda: None, interval_seconds=5)
    assert len(scheduler._jobs) == 1
    assert scheduler._jobs[0].name == "my_job"


def test_tick_runs_due_jobs():
    results = []
    scheduler = PipelineScheduler()
    scheduler.register("counter", lambda: results.append(1), interval_seconds=0)
    scheduler._tick()
    assert len(results) == 1


def test_tick_increments_run_count():
    scheduler = PipelineScheduler()
    scheduler.register("job", lambda: None, interval_seconds=0)
    scheduler._tick()
    assert scheduler._jobs[0].run_count == 1


def test_tick_increments_error_count_on_failure():
    def bad():
        raise RuntimeError("boom")

    scheduler = PipelineScheduler()
    scheduler.register("bad_job", bad, interval_seconds=0)
    scheduler._tick()
    assert scheduler._jobs[0].error_count == 1


def test_job_stats_returns_expected_keys():
    scheduler = PipelineScheduler()
    scheduler.register("stats_job", lambda: None, interval_seconds=30)
    stats = scheduler.job_stats()
    assert len(stats) == 1
    assert "name" in stats[0]
    assert "run_count" in stats[0]
    assert "error_count" in stats[0]
    assert "interval_seconds" in stats[0]


def test_start_stop_does_not_hang():
    scheduler = PipelineScheduler(tick_interval=0.05)
    scheduler.register("noop", lambda: None, interval_seconds=0)
    scheduler.start()
    time.sleep(0.15)
    scheduler.stop()
    assert scheduler._jobs[0].run_count >= 1
