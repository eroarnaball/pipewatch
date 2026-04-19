"""Alert channels and notification dispatch for pipeline metrics."""

from dataclasses import dataclass, field
from typing import List, Optional
from pipewatch.metrics import MetricEvaluation, MetricStatus


@dataclass
class AlertMessage:
    pipeline: str
    metric: str
    status: MetricStatus
    value: float
    message: str

    def format(self) -> str:
        return (
            f"[{self.status.value.upper()}] {self.pipeline}/{self.metric} "
            f"= {self.value} — {self.message}"
        )


class AlertChannel:
    """Base class for alert channels."""

    def send(self, message: AlertMessage) -> None:
        raise NotImplementedError


class ConsoleAlertChannel(AlertChannel):
    """Prints alerts to stdout."""

    def send(self, message: AlertMessage) -> None:
        print(message.format())


class AlertDispatcher:
    def __init__(self, channels: Optional[List[AlertChannel]] = None):
        self.channels: List[AlertChannel] = channels or []

    def add_channel(self, channel: AlertChannel) -> None:
        self.channels.append(channel)

    def dispatch(self, evaluation: MetricEvaluation) -> None:
        if evaluation.status == MetricStatus.OK:
            return
        msg = AlertMessage(
            pipeline=evaluation.metric.pipeline,
            metric=evaluation.metric.name,
            status=evaluation.status,
            value=evaluation.metric.value,
            message=evaluation.message or "",
        )
        for channel in self.channels:
            channel.send(msg)

    def dispatch_all(self, evaluations: List[MetricEvaluation]) -> None:
        for evaluation in evaluations:
            self.dispatch(evaluation)
