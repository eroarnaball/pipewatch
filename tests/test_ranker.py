"""Tests for pipewatch.ranker."""

import pytest
from pipewatch.ranker import MetricRanker, RankedMetric
from pipewatch.metrics import MetricEvaluation, MetricStatus, PipelineMetric


def make_evaluation(name: str, status: MetricStatus, value: float) -> MetricEvaluation:
    metric = PipelineMetric(name=name, value=value)
    return MetricEvaluation(metric=metric, status=status)


def make_ranker(**kwargs) -> MetricRanker:
    return MetricRanker(**kwargs)


def test_rank_empty_returns_empty_list():
    r = make_ranker()
    assert r.rank([]) == []


def test_rank_assigns_sequential_ranks():
    r = make_ranker()
    evs = [
        make_evaluation("a", MetricStatus.OK, 1.0),
        make_evaluation("b", MetricStatus.WARNING, 2.0),
        make_evaluation("c", MetricStatus.CRITICAL, 3.0),
    ]
    ranked = r.rank(evs)
    assert [m.rank for m in ranked] == [1, 2, 3]


def test_critical_ranked_above_warning():
    r = make_ranker(value_weight=0.0, status_weight=1.0)
    evs = [
        make_evaluation("warn", MetricStatus.WARNING, 0.0),
        make_evaluation("crit", MetricStatus.CRITICAL, 0.0),
    ]
    ranked = r.rank(evs)
    assert ranked[0].name == "crit"
    assert ranked[1].name == "warn"


def test_warning_ranked_above_ok():
    r = make_ranker(value_weight=0.0, status_weight=1.0)
    evs = [
        make_evaluation("ok", MetricStatus.OK, 0.0),
        make_evaluation("warn", MetricStatus.WARNING, 0.0),
    ]
    ranked = r.rank(evs)
    assert ranked[0].name == "warn"


def test_value_weight_breaks_tie():
    r = make_ranker(value_weight=1.0, status_weight=0.0)
    evs = [
        make_evaluation("low", MetricStatus.OK, 1.0),
        make_evaluation("high", MetricStatus.OK, 5.0),
    ]
    ranked = r.rank(evs)
    assert ranked[0].name == "high"


def test_top_returns_correct_count():
    r = make_ranker()
    evs = [make_evaluation(f"m{i}", MetricStatus.OK, float(i)) for i in range(10)]
    top = r.top(evs, n=3)
    assert len(top) == 3


def test_top_fewer_than_n_returns_all():
    r = make_ranker()
    evs = [make_evaluation("only", MetricStatus.WARNING, 1.0)]
    top = r.top(evs, n=5)
    assert len(top) == 1


def test_ranked_metric_to_dict_has_expected_keys():
    r = make_ranker()
    evs = [make_evaluation("db", MetricStatus.CRITICAL, 9.9)]
    ranked = r.rank(evs)
    d = ranked[0].to_dict()
    assert "rank" in d
    assert "name" in d
    assert "status" in d
    assert "value" in d
    assert "score" in d


def test_invalid_weights_raise_value_error():
    with pytest.raises(ValueError):
        MetricRanker(value_weight=1.5, status_weight=0.5)


def test_none_value_treated_as_zero():
    r = make_ranker(value_weight=1.0, status_weight=0.0)
    metric = PipelineMetric(name="no_val", value=None)
    ev = MetricEvaluation(metric=metric, status=MetricStatus.OK)
    ranked = r.rank([ev])
    assert ranked[0].value == 0.0
    assert ranked[0].score == 0.0
