"""Tests for pipewatch.scorer."""

import pytest
from pipewatch.scorer import PipelineScorer, HealthScore, MetricScore, _grade
from pipewatch.metrics import PipelineMetric, MetricEvaluation, MetricStatus


def make_evaluation(name: str, value: float, status: MetricStatus) -> MetricEvaluation:
    metric = PipelineMetric(name=name, value=value)
    return MetricEvaluation(metric=metric, status=status)


def test_empty_evaluations_returns_perfect_score():
    scorer = PipelineScorer()
    result = scorer.score([])
    assert result.percentage == 100.0
    assert result.grade == "A"
    assert result.metric_scores == []


def test_all_ok_gives_full_score():
    evals = [
        make_evaluation("a", 1.0, MetricStatus.OK),
        make_evaluation("b", 2.0, MetricStatus.OK),
    ]
    scorer = PipelineScorer()
    result = scorer.score(evals)
    assert result.percentage == 100.0
    assert result.grade == "A"


def test_all_critical_gives_zero_score():
    evals = [
        make_evaluation("a", 1.0, MetricStatus.CRITICAL),
        make_evaluation("b", 2.0, MetricStatus.CRITICAL),
    ]
    scorer = PipelineScorer()
    result = scorer.score(evals)
    assert result.percentage == 0.0
    assert result.grade == "F"
    assert result.total_score == 0.0


def test_mixed_statuses_partial_score():
    evals = [
        make_evaluation("a", 1.0, MetricStatus.OK),
        make_evaluation("b", 2.0, MetricStatus.CRITICAL),
    ]
    scorer = PipelineScorer()
    result = scorer.score(evals)
    assert 0.0 < result.percentage < 100.0


def test_warning_status_gives_half_weight():
    evals = [make_evaluation("x", 1.0, MetricStatus.WARNING)]
    scorer = PipelineScorer()
    result = scorer.score(evals)
    assert result.percentage == pytest.approx(50.0)


def test_custom_weight_applied():
    evals = [
        make_evaluation("critical_metric", 1.0, MetricStatus.CRITICAL),
        make_evaluation("ok_metric", 2.0, MetricStatus.OK),
    ]
    scorer = PipelineScorer(weights={"critical_metric": 5.0, "ok_metric": 1.0})
    result = scorer.score(evals)
    # ok contributes 1.0, critical contributes 0.0; max=6.0
    assert result.total_score == pytest.approx(1.0)
    assert result.max_score == pytest.approx(6.0)


def test_set_weight_validates_range():
    scorer = PipelineScorer()
    with pytest.raises(ValueError):
        scorer.set_weight("m", -1.0)
    with pytest.raises(ValueError):
        scorer.set_weight("m", 11.0)


def test_set_weight_updates_scorer():
    scorer = PipelineScorer()
    scorer.set_weight("m", 3.0)
    evals = [make_evaluation("m", 1.0, MetricStatus.OK)]
    result = scorer.score(evals)
    assert result.max_score == pytest.approx(3.0)


def test_to_dict_has_expected_keys():
    evals = [make_evaluation("a", 1.0, MetricStatus.OK)]
    result = PipelineScorer().score(evals)
    d = result.to_dict()
    assert "total_score" in d
    assert "max_score" in d
    assert "percentage" in d
    assert "grade" in d
    assert "metric_scores" in d
    assert isinstance(d["metric_scores"], list)


def test_grade_thresholds():
    assert _grade(95) == "A"
    assert _grade(80) == "B"
    assert _grade(60) == "C"
    assert _grade(30) == "D"
    assert _grade(10) == "F"
