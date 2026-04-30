"""Metric name mapping and aliasing for pipewatch."""
from dataclasses import dataclass, field
from typing import Dict, Optional, List


@dataclass
class MappingEntry:
    canonical: str
    aliases: List[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "canonical": self.canonical,
            "aliases": list(self.aliases),
            "description": self.description,
        }


class MetricMapper:
    """Maps metric aliases to canonical names."""

    def __init__(self) -> None:
        self._entries: Dict[str, MappingEntry] = {}
        self._alias_index: Dict[str, str] = {}

    def register(self, canonical: str, aliases: Optional[List[str]] = None, description: str = "") -> MappingEntry:
        aliases = aliases or []
        entry = MappingEntry(canonical=canonical, aliases=aliases, description=description)
        self._entries[canonical] = entry
        for alias in aliases:
            self._alias_index[alias] = canonical
        return entry

    def resolve(self, name: str) -> Optional[str]:
        """Return canonical name for a given name or alias."""
        if name in self._entries:
            return name
        return self._alias_index.get(name)

    def add_alias(self, canonical: str, alias: str) -> bool:
        if canonical not in self._entries:
            return False
        self._entries[canonical].aliases.append(alias)
        self._alias_index[alias] = canonical
        return True

    def remove_alias(self, alias: str) -> bool:
        if alias not in self._alias_index:
            return False
        canonical = self._alias_index.pop(alias)
        if canonical in self._entries and alias in self._entries[canonical].aliases:
            self._entries[canonical].aliases.remove(alias)
        return True

    def all_entries(self) -> List[MappingEntry]:
        return list(self._entries.values())

    def get(self, canonical: str) -> Optional[MappingEntry]:
        return self._entries.get(canonical)
