"""Simple interval-based scheduler for periodic metric collection."""

import time
import threading
from typing import Callable, Optional


class ScheduledJob:
    def __init__(self, name: str, fn: Callable, interval_seconds: float):
        self.name = name
        self.fn = fn
        self.interval_seconds = interval_seconds
        self.last_run: Optional[float] = None
        self.run_count: int = 0
        self.error_count: int = 0

    def is_due(self, now: float) -> bool:
        if self.last_run is None:
            return True
        return (now - self.last_run) >= self.interval_seconds


class PipelineScheduler:
    def __init__(self, tick_interval: float = 1.0):
        self._jobs: list[ScheduledJob] = []
        self._tick_interval = tick_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def register(self, name: str, fn: Callable, interval_seconds: float) -> None:
        job = ScheduledJob(name=name, fn=fn, interval_seconds=interval_seconds)
        self._jobs.append(job)

    def _tick(self) -> None:
        now = time.monotonic()
        for job in self._jobs:
            if job.is_due(now):
                try:
                    job.fn()
                    job.run_count += 1
                except Exception:
                    job.error_count += 1
                finally:
                    job.last_run = time.monotonic()

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self) -> None:
        while self._running:
            self._tick()
            time.sleep(self._tick_interval)

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def job_stats(self) -> list[dict]:
        return [
            {"name": j.name, "run_count": j.run_count, "error_count": j.error_count,
             "interval_seconds": j.interval_seconds, "last_run": j.last_run}
            for j in self._jobs
        ]
