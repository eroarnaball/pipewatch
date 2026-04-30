"""Tests for pipewatch.mapper."""
import pytest
from pipewatch.mapper import MetricMapper, MappingEntry


def make_mapper() -> MetricMapper:
    m = MetricMapper()
    m.register("row_count", aliases=["rows", "record_count"], description="Row count")
    m.register("latency_ms", aliases=["latency"], description="Latency")
    return m


def test_register_returns_entry():
    m = MetricMapper()
    entry = m.register("row_count", aliases=["rows"])
    assert isinstance(entry, MappingEntry)
    assert entry.canonical == "row_count"
    assert "rows" in entry.aliases


def test_resolve_canonical_name_returns_itself():
    m = make_mapper()
    assert m.resolve("row_count") == "row_count"


def test_resolve_alias_returns_canonical():
    m = make_mapper()
    assert m.resolve("rows") == "row_count"
    assert m.resolve("record_count") == "row_count"


def test_resolve_unknown_returns_none():
    m = make_mapper()
    assert m.resolve("nonexistent") is None


def test_add_alias_updates_index():
    m = make_mapper()
    result = m.add_alias("latency_ms", "lag")
    assert result is True
    assert m.resolve("lag") == "latency_ms"


def test_add_alias_unknown_canonical_returns_false():
    m = make_mapper()
    result = m.add_alias("ghost_metric", "ghost")
    assert result is False


def test_remove_alias_removes_from_index():
    m = make_mapper()
    result = m.remove_alias("rows")
    assert result is True
    assert m.resolve("rows") is None


def test_remove_alias_also_removes_from_entry():
    m = make_mapper()
    m.remove_alias("rows")
    entry = m.get("row_count")
    assert "rows" not in entry.aliases


def test_remove_nonexistent_alias_returns_false():
    m = make_mapper()
    assert m.remove_alias("does_not_exist") is False


def test_all_entries_returns_all():
    m = make_mapper()
    entries = m.all_entries()
    assert len(entries) == 2


def test_get_returns_entry_for_known():
    m = make_mapper()
    entry = m.get("latency_ms")
    assert entry is not None
    assert entry.canonical == "latency_ms"


def test_get_returns_none_for_unknown():
    m = make_mapper()
    assert m.get("unknown") is None


def test_to_dict_has_expected_keys():
    m = make_mapper()
    d = m.get("row_count").to_dict()
    assert "canonical" in d
    assert "aliases" in d
    assert "description" in d
