"""Tests for pipewatch.tagger."""
import pytest
from pipewatch.tagger import MetricTagger, TaggedMetric


def make_tagger() -> MetricTagger:
    return MetricTagger()


def test_tag_creates_entry():
    t = make_tagger()
    m = t.tag("cpu", {"env": "prod", "team": "infra"})
    assert m.name == "cpu"
    assert m.tags["env"] == "prod"


def test_tag_updates_existing():
    t = make_tagger()
    t.tag("cpu", {"env": "prod"})
    t.tag("cpu", {"region": "us-east"})
    m = t.get("cpu")
    assert m.tags["env"] == "prod"
    assert m.tags["region"] == "us-east"


def test_get_returns_none_for_unknown():
    t = make_tagger()
    assert t.get("missing") is None


def test_has_tag_key_only():
    m = TaggedMetric(name="m", tags={"env": "prod"})
    assert m.has_tag("env")
    assert not m.has_tag("region")


def test_has_tag_key_and_value():
    m = TaggedMetric(name="m", tags={"env": "prod"})
    assert m.has_tag("env", "prod")
    assert not m.has_tag("env", "staging")


def test_filter_by_tag_key():
    t = make_tagger()
    t.tag("cpu", {"env": "prod"})
    t.tag("mem", {"env": "staging"})
    t.tag("disk", {"team": "infra"})
    results = t.filter_by_tag("env")
    names = {m.name for m in results}
    assert names == {"cpu", "mem"}


def test_filter_by_tag_key_and_value():
    t = make_tagger()
    t.tag("cpu", {"env": "prod"})
    t.tag("mem", {"env": "staging"})
    results = t.filter_by_tag("env", "prod")
    assert len(results) == 1
    assert results[0].name == "cpu"


def test_untag_removes_key():
    t = make_tagger()
    t.tag("cpu", {"env": "prod", "team": "infra"})
    t.untag("cpu", ["team"])
    m = t.get("cpu")
    assert "team" not in m.tags
    assert "env" in m.tags


def test_all_tags_returns_union():
    t = make_tagger()
    t.tag("cpu", {"env": "prod"})
    t.tag("mem", {"team": "infra"})
    assert t.all_tags() == {"env", "team"}


def test_to_dict_structure():
    m = TaggedMetric(name="cpu", tags={"env": "prod"})
    d = m.to_dict()
    assert d["name"] == "cpu"
    assert d["tags"] == {"env": "prod"}
