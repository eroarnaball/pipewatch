"""Tests for pipewatch.watchdog."""

from datetime import datetime, timedelta
import pytest
from pipewatch.watchdog import MetricWatchdog, StalenessReport


def make_watchdog(default_ttl: int = 60) -> MetricWatchdog:
    return MetricWatchdog(default_ttl=default_ttl)


def test_check_returns_none_when_never_touched():
    wd = make_watchdog()
    wd.register("cpu")
    assert wd.check("cpu") is None


def test_touch_and_check_not_stale():
    wd = make_watchdog(default_ttl=60)
    now = datetime.utcnow()
    wd.register("cpu")
    wd.touch("cpu", at=now)
    report = wd.check("cpu", now=now)
    assert report is not None
    assert not report.is_stale


def test_metric_becomes_stale_after_ttl():
    wd = make_watchdog(default_ttl=30)
    past = datetime.utcnow() - timedelta(seconds=60)
    wd.register("cpu")
    wd.touch("cpu", at=past)
    report = wd.check("cpu")
    assert report.is_stale
    assert report.age_seconds >= 60


def test_per_metric_ttl_override():
    wd = make_watchdog(default_ttl=300)
    past = datetime.utcnow() - timedelta(seconds=10)
    wd.register("fast_metric", ttl=5)
    wd.touch("fast_metric", at=past)
    report = wd.check("fast_metric")
    assert report.is_stale


def test_check_all_returns_all_registered_touched():
    wd = make_watchdog()
    now = datetime.utcnow()
    for name in ["a", "b", "c"]:
        wd.register(name)
        wd.touch(name, at=now)
    reports = wd.check_all(now=now)
    assert len(reports) == 3


def test_stale_metrics_filters_correctly():
    wd = make_watchdog(default_ttl=60)
    now = datetime.utcnow()
    wd.register("fresh")
    wd.touch("fresh", at=now)
    wd.register("stale")
    wd.touch("stale", at=now - timedelta(seconds=120))
    stale = wd.stale_metrics(now=now)
    assert len(stale) == 1
    assert stale[0].metric_name == "stale"


def test_to_dict_has_expected_keys():
    wd = make_watchdog(default_ttl=60)
    now = datetime.utcnow()
    wd.register("mem")
    wd.touch("mem", at=now)
    d = wd.check("mem", now=now).to_dict()
    for key in ["metric_name", "last_seen", "ttl_seconds", "age_seconds", "is_stale"]:
        assert key in d
