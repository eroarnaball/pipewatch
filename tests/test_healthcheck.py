import pytest
from pipewatch.healthcheck import HealthChecker, HealthCheckResult, HealthSummary
from pipewatch.metrics import MetricStatus


def make_checker() -> HealthChecker:
    checker = HealthChecker()
    checker.register("ok_check", lambda: (MetricStatus.OK, "all good"))
    checker.register("warn_check", lambda: (MetricStatus.WARNING, "watch out"))
    checker.register("crit_check", lambda: (MetricStatus.CRITICAL, "broken"))
    return checker


def test_run_returns_none_for_unknown_check():
    checker = HealthChecker()
    assert checker.run("nonexistent") is None


def test_run_returns_result_for_known_check():
    checker = make_checker()
    result = checker.run("ok_check")
    assert isinstance(result, HealthCheckResult)
    assert result.name == "ok_check"
    assert result.status == MetricStatus.OK
    assert result.message == "all good"


def test_run_all_returns_summary_with_all_results():
    checker = make_checker()
    summary = checker.run_all()
    assert isinstance(summary, HealthSummary)
    assert len(summary.results) == 3


def test_overall_ok_when_all_ok():
    checker = HealthChecker()
    checker.register("a", lambda: (MetricStatus.OK, "fine"))
    checker.register("b", lambda: (MetricStatus.OK, "fine"))
    summary = checker.run_all()
    assert summary.overall == MetricStatus.OK


def test_overall_warning_when_any_warning():
    checker = HealthChecker()
    checker.register("a", lambda: (MetricStatus.OK, "fine"))
    checker.register("b", lambda: (MetricStatus.WARNING, "warn"))
    summary = checker.run_all()
    assert summary.overall == MetricStatus.WARNING


def test_overall_critical_takes_priority():
    checker = make_checker()
    summary = checker.run_all()
    assert summary.overall == MetricStatus.CRITICAL


def test_failed_excludes_ok_results():
    checker = make_checker()
    summary = checker.run_all()
    names = {r.name for r in summary.failed}
    assert "ok_check" not in names
    assert "warn_check" in names
    assert "crit_check" in names


def test_exception_in_check_returns_critical():
    checker = HealthChecker()
    checker.register("boom", lambda: (_ for _ in ()).throw(RuntimeError("oops")))
    result = checker.run("boom")
    assert result is not None
    assert result.status == MetricStatus.CRITICAL
    assert "oops" in result.message


def test_to_dict_has_expected_keys():
    checker = make_checker()
    summary = checker.run_all()
    d = summary.to_dict()
    assert "overall" in d
    assert "total" in d
    assert "failed_count" in d
    assert "results" in d
    assert d["total"] == 3


def test_result_to_dict_has_expected_keys():
    checker = make_checker()
    result = checker.run("ok_check")
    d = result.to_dict()
    assert "name" in d
    assert "status" in d
    assert "message" in d
    assert "checked_at" in d
