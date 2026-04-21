import pytest
from datetime import datetime, timedelta
from pipewatch.ratelimiter import RateLimitEntry, AlertRateLimiter


def make_limiter(max_alerts=3, window=60) -> AlertRateLimiter:
    return AlertRateLimiter(default_max=max_alerts, default_window=window)


def test_first_alert_is_allowed():
    limiter = make_limiter()
    assert limiter.allow("my_metric") is True


def test_alerts_within_limit_are_allowed():
    limiter = make_limiter(max_alerts=3)
    now = datetime.utcnow()
    assert limiter.allow("m", now=now) is True
    assert limiter.allow("m", now=now) is True
    assert limiter.allow("m", now=now) is True


def test_alert_exceeding_limit_is_blocked():
    limiter = make_limiter(max_alerts=2)
    now = datetime.utcnow()
    limiter.allow("m", now=now)
    limiter.allow("m", now=now)
    assert limiter.allow("m", now=now) is False


def test_old_alerts_outside_window_are_pruned():
    limiter = make_limiter(max_alerts=2, window=60)
    old = datetime.utcnow() - timedelta(seconds=120)
    now = datetime.utcnow()
    limiter.allow("m", now=old)
    limiter.allow("m", now=old)
    # Old entries should be pruned, so new alert should be allowed
    assert limiter.allow("m", now=now) is True


def test_remaining_decreases_with_each_alert():
    limiter = make_limiter(max_alerts=3)
    now = datetime.utcnow()
    limiter.allow("m", now=now)
    limiter.allow("m", now=now)
    status = limiter.status("m")
    assert status["remaining"] == 1


def test_is_limited_true_when_at_max():
    entry = RateLimitEntry("x", max_alerts=2, window_seconds=60)
    now = datetime.utcnow()
    entry.record(now)
    entry.record(now)
    assert entry.is_limited(now) is True


def test_configure_overrides_defaults():
    limiter = make_limiter(max_alerts=10, window=300)
    limiter.configure("special", max_alerts=1, window_seconds=30)
    now = datetime.utcnow()
    assert limiter.allow("special", now=now) is True
    assert limiter.allow("special", now=now) is False


def test_reset_clears_counter():
    limiter = make_limiter(max_alerts=1)
    now = datetime.utcnow()
    limiter.allow("m", now=now)
    assert limiter.allow("m", now=now) is False
    limiter.reset("m")
    assert limiter.allow("m", now=now) is True


def test_reset_unknown_metric_returns_false():
    limiter = make_limiter()
    assert limiter.reset("nonexistent") is False


def test_status_returns_none_for_unknown():
    limiter = make_limiter()
    assert limiter.status("ghost") is None


def test_all_statuses_returns_list():
    limiter = make_limiter()
    limiter.allow("a")
    limiter.allow("b")
    statuses = limiter.all_statuses()
    names = [s["metric_name"] for s in statuses]
    assert "a" in names
    assert "b" in names


def test_to_dict_has_expected_keys():
    entry = RateLimitEntry("test", max_alerts=5, window_seconds=120)
    d = entry.to_dict()
    for key in ["metric_name", "max_alerts", "window_seconds", "current_count", "remaining", "is_limited"]:
        assert key in d
