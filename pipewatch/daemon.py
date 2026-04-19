"""Daemon entry point that wires collector, scheduler, alerts, and history."""

from typing import Optional
from pipewatch.collector import MetricCollector
from pipewatch.scheduler import PipelineScheduler
from pipewatch.thresholds import ThresholdEvaluator
from pipewatch.alerts import AlertDispatcher
from pipewatch.history import MetricHistory
from pipewatch.reporter import RunReport


class PipeWatchDaemon:
    def __init__(
        self,
        collector: MetricCollector,
        evaluator: ThresholdEvaluator,
        dispatcher: AlertDispatcher,
        history: Optional[MetricHistory] = None,
        interval_seconds: float = 60.0,
        tick_interval: float = 1.0,
    ):
        self.collector = collector
        self.evaluator = evaluator
        self.dispatcher = dispatcher
        self.history = history or MetricHistory()
        self.interval_seconds = interval_seconds
        self._scheduler = PipelineScheduler(tick_interval=tick_interval)
        self._scheduler.register(
            name="collect_and_evaluate",
            fn=self._run_cycle,
            interval_seconds=interval_seconds,
        )
        self._last_report: Optional[RunReport] = None

    def _run_cycle(self) -> None:
        metrics = self.collector.collect_all()
        evaluations = [self.evaluator.evaluate(m) for m in metrics]
        report = RunReport(evaluations)
        self._last_report = report
        for ev in evaluations:
            self.history.record(ev)
            self.dispatcher.dispatch(ev)

    def start(self) -> None:
        self._scheduler.start()

    def stop(self) -> None:
        self._scheduler.stop()

    @property
    def last_report(self) -> Optional[RunReport]:
        return self._last_report

    def scheduler_stats(self) -> list[dict]:
        return self._scheduler.job_stats()
